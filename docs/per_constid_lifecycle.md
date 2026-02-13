# Per-ConstID Lifecycle Management

## 问题

原有架构中，`xk-kfuncs.ko` 在每次 `load` 时 `insmod`、`unload` 时 `rmmod`，且一致性模式 `kMode` 和全局转换标志 `ir_kprobes_on` 是内核模块的全局变量。所有 BPF 程序通过 kfunc 调用读取这两个值。这导致：

1. **无法增量加载** — `insmod` 在模块已加载时失败，无法为第二个 ConstID 加载 BPF 程序
2. **无法单独卸载** — 所有 BPF 程序 pin 在同一个 `/sys/fs/bpf/xkernel/` 目录下，`rm -rf` 会删除全部
3. **模式全局共享** — `kMode` 是模块参数，所有 ConstID 被迫使用相同的一致性模式
4. **Mode 2 转换全局生效** — `ir_kprobes_on = true` 影响所有 ConstID，无法独立控制激活状态

## 设计思路

核心思路：**将 mode 和 activation 状态从内核模块全局变量移入 per-BPF-program BSS 变量**。

### 为什么选择 BSS 变量

BPF 的 BSS（Block Started by Symbol）section 是 per-object-file 的。当使用自定义 section 名（如 `SEC(".bss.xk_mode")`）时，每个编译单元（.bpf.o 文件）会拥有独立的 BSS map。配合 `bpftool prog loadall ... pinmaps` 将 map pin 到独立路径，userspace 就可以通过 `bpftool map update pinned <path>` 精确控制每个 ConstID 的状态，无需任何内核模块改动。

与 kfunc 方案的对比：

| | kfunc（旧） | BSS 变量（新） |
|---|---|---|
| 状态位置 | 内核模块全局变量 | per-BPF-program BSS section |
| 读取方式 | BPF 调用 kfunc → 内核函数调用 | BPF 直接读内存（零开销） |
| 粒度 | 全局唯一 | 每个 ConstID 独立 |
| 写入方式 | 需要内核接口 | userspace 通过 bpftool map update |

### Pin 目录结构

每个 ConstID 使用独立的 pin 目录：

```
/sys/fs/bpf/xkernel/
    1/                     ← ConstID 1
        progs/             ← BPF 程序 pin
        maps/              ← Map pin（含 .bss.xk_mode, .bss.xk_active, cs_map 等）
    2/                     ← ConstID 2
        progs/
        maps/
```

这样 `rm -rf /sys/fs/bpf/xkernel/1/` 只影响 ConstID 1，ConstID 2 完全不受影响。

### Runtime State

引入 `/dev/shm/xkernel/runtime_state`（JSON）记录运行时状态，使工具能感知当前哪些 ConstID 已加载、使用什么模式：

```json
{
    "kfuncs_loaded": true,
    "active_const_ids": {
        "1": {"mode": 0, "bpf_file": "policy_1.bpf.o", "status": "active"},
        "2": {"mode": 2, "bpf_file": "policy_2.bpf.o", "status": "active"}
    }
}
```

## 实现细节

### 文件 1：`bpf/xkernel.bpf.h`

添加两个 BSS 变量，每个放在独立的 section 中：

```c
SEC(".bss.xk_mode")   int xk_mode = 0;    // 0=Immediate, 1=Per-task, 2=Global
SEC(".bss.xk_active")  int xk_active = 0;   // 0=未激活, 1=已激活
```

重写 `transition_done()` 和 `global_transition_done()`，将 kfunc 调用替换为直接读 BSS：

- `global_transition_done()`: `kfuncs_is_ir_kprobes_on()` → `xk_active == 1`
- `transition_done()`: `kfuncs_get_consistency_mode()` → 直接读 `xk_mode`

kfunc 声明保留不动（`bpf_probe_write_kernel` 仍在使用）。

### 文件 2：`kernel/kfuncs/kfuncs.c`

仅将 `kMode` 默认值从 2 改为 0。模块不再需要传 `kMode=X` 参数，因为 mode 现在在 BPF 侧管理。kfunc 函数和 EXPORT_SYMBOL 全部保留，保持向后兼容。

### 文件 3：`xkernel/loader.py`

新增 per-ConstID 基础设施函数：

| 函数 | 作用 |
|------|------|
| `is_kfuncs_loaded()` | 通过 `lsmod` 检查模块是否已加载 |
| `ensure_kfuncs_loaded()` | 幂等加载：已加载则跳过，未加载则 insmod |
| `collect_map_info()` | 通过 pinned program → map_ids 关联发现所有 map，构建 name→id 映射 |
| `update_map_by_id()` | 通过 `bpftool map update id <ID>` 更新 map |
| `set_bss_variable()` | 通过 map_info 查找 map ID，再用 `update_map_by_id` 写入 BSS 变量 |
| `load_and_attach_per_constid()` | 创建 per-ConstID pin 目录，loadall + pinmaps，collect_map_info，设置 xk_mode（mode 0 时同时设 xk_active=1）。返回 `(ret, map_info)` |
| `activate_constid()` | 设置 xk_active=1（接受可选 map_info 参数） |
| `unload_constid()` | rm -rf 对应 pin 目录，更新 runtime state |
| `load_critical_spans_for_constid()` | 用 map ID 更新 cs_len 和 cs_map（接受可选 map_info 参数） |
| `get_runtime_state()` / `save_runtime_state()` | JSON 读写 |

关键改动：BSS maps（`.bss.*`）不会被 `bpftool prog loadall ... pinmaps` 自动 pin（它们是 libbpf internal maps）。因此不能用 `pinned` 路径访问。改为通过 `bpftool prog show pinned <prog_path> -j` 获取 program 关联的 `map_ids`，再用 `bpftool map show id <ID> -j` 查询 map name，构建 `name → id` 映射，最后用 `bpftool map update id <ID>` 更新。这种方式对所有 map 类型（BSS、array、hash 等）统一有效。

### 文件 4：`xkernel/cli.py`

**`cmd_load` 重写**（单 ConstID 加载流程）：

```
解析参数 (mode, constID)
  → ensure_kfuncs_loaded()            # 幂等
  → 检查 ConstID 未在 active_const_ids 中
  → 解析 ConstID → BPF 文件
  → 生成 CS 文件（仅此 ConstID）
  → 生成 cs_artifact.bpf.h → 编译 BPF
  → [可选: --jump-opt 探测优化]
  → load_and_attach_per_constid()     # per-ConstID pin + 设 xk_mode
  → load_critical_spans_for_constid() # pinned 路径
  → Mode 2: insmod consistency → 等待 → activate → rmmod consistency
  → 更新 scope_table + runtime_state
```

**`cmd_unload` 重写**：

- `unload <constID>`：仅卸载指定 ConstID（rm -rf 其 pin 目录），如果无更多 active ConstID 则 rmmod kfuncs
- `unload --all`：遍历卸载所有 active ConstID，然后 rmmod kfuncs

**新增 `cmd_status`**：读取 runtime state，展示 kfuncs 加载状态和各 ConstID 的 mode/status。

## Mode 2 关键机制

consistency 模块仍然设置全局 `ir_kprobes_on = true`，但新的 BPF 代码不再读取它。BPF 程序只读 per-program `xk_active`。因此 Mode 2 的流程变为：

1. `insmod xk-consistency.ko` → 内核完成 stop-machine 转换 → `ir_kprobes_on = true`
2. userspace 检测转换完成后，设置该 ConstID 的 `xk_active = 1`
3. `rmmod xk-consistency` → `ir_kprobes_on = false`（对 BPF 无影响）
4. 为另一个 ConstID 做 Mode 2 时，重新 `insmod`，独立转换

## 示例流程

```bash
# 加载 ConstID 1（Immediate）
$ ./xkernel-tool load 0 1
  insmod xk-kfuncs.ko              # 首次加载
  bpftool loadall → /sys/fs/bpf/xkernel/1/{progs,maps}
  xk_mode=0, xk_active=1           # 立即生效

# 加载 ConstID 2（Global, 5s timeout）
$ ./xkernel-tool load 2 2 5
  (kfuncs 已加载，跳过)
  bpftool loadall → /sys/fs/bpf/xkernel/2/{progs,maps}
  xk_mode=2, xk_active=0           # 等待转换
  insmod xk-consistency.ko kTimeout=5
  (转换完成) → xk_active=1 → rmmod xk-consistency

# 查看状态
$ ./xkernel-tool status
  kfuncs module: loaded
  ConstID 1: mode=Immediate, active
  ConstID 2: mode=Global, active

# 单独卸载 ConstID 1
$ ./xkernel-tool unload 1           # ConstID 2 不受影响

# 全部卸载
$ ./xkernel-tool unload --all       # rmmod kfuncs
```
