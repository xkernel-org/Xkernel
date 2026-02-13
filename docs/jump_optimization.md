# Kprobe Jump Optimization

## 背景

Linux kprobe 的默认实现使用 INT3 断点指令（~115ns），但当探测点满足对齐和间距要求时，内核可以将其优化为 5 字节 JMP 跳转指令（~25ns），延迟降低约 4-5 倍。

此前 codegen 对每个 kprobe 只选取一个固定偏移（`[*]` 标记指令的下一条指令地址）。本次改动计算所有等效的候选偏移，并在加载时逐一尝试，选取能被内核 jump-optimize 的偏移。

## 核心思路

### 候选窗口

一个 kprobe 的作用是在目标指令执行前，通过 BPF 程序覆写目标寄存器的值。因此，kprobe 的挂载点不必局限于被修改指令的紧邻下一条——只要挂在"目标寄存器首次被读取"之前（含该读取指令本身），效果都是等价的。

```
[*] 39b: mov $0x3,%esi    ← 被修改的指令，写 %esi
    3a0: mov %rbx,%rdi    ← 候选 1（不读 esi）
    3a3: call ...          ← 候选 2（call 隐式读 esi，窗口结束）
```

候选窗口 = `[changed_instruction + 1, first_reader_of_target_register]`（闭区间）。

### 寄存器读取判定

对 AT&T 语法指令的分析规则：

| 指令类型 | 读取规则 |
|---------|---------|
| `mov`/`lea`/`movzbl` 等 | 只读源操作数；目标操作数为纯写（但目标中的内存寻址基址/变址寄存器算读） |
| `cmp`/`test` | 读取所有操作数 |
| `add`/`sub`/`imul`/`shr`/`xor` 等 | 读取所有操作数（目标是 read-modify-write） |
| `call` | 隐式读取参数寄存器 `rdi, rsi, rdx, rcx, r8, r9` |

寄存器按"族"归类（如 `eax`/`rax`/`ax`/`al`/`ah` 同属 `ax` 族），匹配时使用族级别的检查。

## 实现

改动涉及三个文件，沿着"生成 → 编译 → 加载"的流水线方向传递候选信息。

### 1. `xkernel/codegen.py` — 计算候选偏移

**新增函数：**

- `get_register_family(reg_name)` — 将任意 x86-64 寄存器名映射到规范族名
- `_split_asm_operands(operand_str)` — 按逗号拆分 AT&T 操作数，尊重括号嵌套
- `instruction_reads_register(inst_line, reg_family)` — 判断一条指令是否读取指定寄存器族

**修改逻辑：**

`extract_all_basic_blocks_from_file()` 中，原来找到 `[*]` 后只取下一条指令地址作为 `kprobe_addr`。改为继续向下扫描，将每条指令地址加入 `candidate_addrs`，直到遇到首个读取目标寄存器的指令（包含该指令）或 Basic Block 边界为止。

```python
# 伪代码
candidate_addrs = []
target_family = get_register_family(目标寄存器)
for 后续每条指令:
    candidate_addrs.append(指令地址)
    if instruction_reads_register(指令, target_family):
        break  # 包含此读取者，然后停止
```

候选地址在偏移转换阶段同步转为函数内偏移 `candidate_offsets`，并沿流水线传递：

```
BB文件 → extract_all_basic_blocks_from_file (candidate_addrs/candidate_offsets)
       → analyze_linear_relationship (generated_kprobes[].candidate_offsets)
       → generate_multi_kprobe_bpf_file (写入 // Candidates: 注释)
       → add_scope_table_entry_multi_cs (写入 Candidates 列)
```

生成的 BPF 文件中，每个 kprobe 的 SEC 注释前会插入候选列表：

```c
// Candidates: 0x3a0,0x3a3
SEC("kprobe/blk_mq_dispatch_rq_list+0x3a0")
```

### 2. `xkernel/loader.py` — 加载时探测优化

**新增函数：**

- `compile_single_bpf(bpf_c_path, bpf_dir)` — 编译单个 BPF 源文件
- `check_kprobe_optimized(func_name, offset)` — 读取 `/sys/kernel/debug/kprobes/list`，检查 `[OPTIMIZED]` 标记
- `patch_bpf_sec_offset(bpf_c_path, func_name, old, new)` — 替换源文件中的 SEC 注释和 BPF_KPROBE 函数名
- `try_jump_optimization(bpf_c_path, bpf_dir)` — 核心算法

**`try_jump_optimization` 流程：**

```
1. 解析 BPF .c 文件，提取每个 kprobe 的 Candidates 注释和当前 SEC 偏移
2. 对每个有多个候选的 kprobe:
   a. 依次尝试每个候选偏移:
      - patch SEC 注释 → 编译 → bpftool loadall autoattach
      - 等待 0.5s 后读取 /sys/kernel/debug/kprobes/list
      - 如果标记为 [OPTIMIZED]: 选中该偏移，卸载测试探针，进入下个 kprobe
      - 否则: 卸载，尝试下一个候选
   b. 如果没有任何候选被优化，保留原始偏移（第一个候选）
3. 用选定的偏移做最终编译
```

测试探针挂载在临时 pin 目录 `/sys/fs/bpf/xkernel_jumpopt_test`，与正式加载路径隔离。原始源文件在操作前备份，失败时自动恢复。

### 3. `xkernel/cli.py` — 用户接口

在 `cmd_load()` 中新增 `--jump-opt` 标志。该标志在 cs_artifact 生成和 BPF 编译完成后、内核模块加载前生效：

```
xkernel-tool load --jump-opt 0 1
```

流程插入点：

```
生成 cs_artifact → 编译 BPF → [--jump-opt: 探测优化] → insmod → loadall → 加载 CS
```

## 数据流

```
                codegen                          loader (--jump-opt)
                  │                                    │
  BB文件 ──→ candidate_offsets ──→ BPF .c 文件        │
                  │                 (// Candidates)    │
                  │                      │             │
                  ├──→ scope_table       └──→ 逐候选尝试 ──→ patch SEC
                  │    (Candidates列)         ↓              ↓
                  │                      bpftool load    check OPTIMIZED
                  │                           ↓              ↓
                  │                      bpftool unload  选中/下一个
                  │                           ↓
                  │                      最终编译 ──→ 正式加载
```

## 候选窗口验证

| 测试用例 | 函数 | 目标寄存器 | 候选偏移 | 窗口终止原因 |
|---------|------|-----------|---------|------------|
| TC1 | cubictcp_acked | %eax | `[0x205]` | cmp 立即读 eax |
| TC2 | blk_mq_dispatch_rq_list | %esi | `[0x3a0, 0x3a3]` | call 隐式读 esi |
| TC3/BB1 | io_cqring_wait | %ecx | `[0x7a, 0x7d, 0x80]` | cmp 读 ecx |
| TC3/BB3 | __do_sys_io_uring_enter | %eax | `[0x52c, 0x530, 0x533, 0x53a]` | cmp 读 eax |
| TC4 | tcp_rack_detect_loss | %r15d | `[0x7e]` | imul 立即读 r15d |
| TC5/BB1 | __blk_mq_sched_dispatch | %esi | `[0x59a, 0x59d, 0x5a0]` | call 隐式读 esi |

## 使用方式

```bash
# 构建（生成含候选信息的 BPF 文件）
./xkernel-tool build

# 检查候选信息
grep "Candidates:" bpf/examples/my_policy_*.bpf.c

# 带 jump 优化加载
./xkernel-tool load --jump-opt 0 1

# 验证优化状态
sudo cat /sys/kernel/debug/kprobes/list | grep OPTIMIZED

# 不带优化加载（向后兼容）
./xkernel-tool load 0 1
```
