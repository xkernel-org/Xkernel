# Kprobe Jump Optimization

## Background

The default kprobe implementation uses an INT3 breakpoint (~115 ns). When the probe site meets
alignment and size requirements, the kernel can instead patch it with a 5-byte `jmp rel32` to an
out-of-line trampoline (~25 ns) — roughly 4–5× lower overhead.

Previously, codegen picked a single fixed offset for each kprobe (the instruction immediately
after the `[*]`-marked seed). This change computes all equivalent candidate offsets and probes
each one at load time, selecting the one the kernel actually jump-optimizes.

## Core Idea

### Candidate Window

A kprobe's job is to overwrite a target register before it is consumed. The probe does not have
to fire at the instruction immediately after the seed — any attachment point between the seed and
the first instruction that **reads** the target register (inclusive) is equivalent.

```
[*] 39b: mov $0x3,%esi    ← seed, writes %esi
    3a0: mov %rbx,%rdi    ← candidate 1 (does not read %esi)
    3a3: call ...          ← candidate 2 (call implicitly reads %esi — window ends here)
```

Candidate window = `[seed + 1, first_reader_of_target_register]` (closed interval).

### Register-Read Detection

Rules for AT&T-syntax instructions:

| Instruction class | Read rule |
|-------------------|-----------|
| `mov`, `lea`, `movzbl`, etc. | Reads source operand only; destination is write-only (but base/index registers in a memory destination count as reads) |
| `cmp`, `test` | Reads all operands |
| `add`, `sub`, `imul`, `shr`, `xor`, etc. | Reads all operands (destination is read-modify-write) |
| `call` | Implicitly reads argument registers `rdi, rsi, rdx, rcx, r8, r9` |

Registers are grouped into families (e.g. `eax`/`rax`/`ax`/`al`/`ah` all belong to the `ax`
family); matching is done at the family level.

## Implementation

The change spans three files along the generate → compile → load pipeline.

### 1. `xkernel/codegen.py` — Computing Candidate Offsets

**New functions:**

- `get_register_family(reg_name)` — maps any x86-64 register name to its canonical family name
- `_split_asm_operands(operand_str)` — splits AT&T operands on commas, respecting parentheses
- `instruction_reads_register(inst_line, reg_family)` — returns True if the instruction reads the given register family
- `get_insn_byte_count(inst_line)` — counts raw instruction bytes from a BB file line (hex tokens between `<addr>:` and the tab)
- `check_jump_optimizable(all_insts, idx)` — checks whether a candidate position supports kprobe jump optimization (see below)

**Modified logic:**

In `extract_all_basic_blocks_from_file()`, after finding the `[*]` seed, instead of taking only
the next instruction address, the code scans forward and collects every instruction address into
`candidate_addrs` until it hits the first register reader (inclusive) or the basic block boundary.

```python
# pseudocode
candidate_addrs = []
target_family = get_register_family(target_register)
for each subsequent instruction:
    candidate_addrs.append(instruction_address)
    if instruction_reads_register(instruction, target_family):
        break  # include this reader, then stop
```

Candidate addresses are converted to function-relative offsets (`candidate_offsets`) and
propagated through the pipeline:

```
BB file → extract_all_basic_blocks_from_file  (candidate_addrs / candidate_offsets)
        → analyze_linear_relationship          (generated_kprobes[].candidate_offsets)
        → generate_multi_kprobe_bpf_file       (writes // Candidates: comment)
        → add_scope_table_entry_multi_cs       (writes Candidates column)
```

The generated BPF file includes the candidate list before each kprobe's SEC annotation:

```c
// Candidates: 0x3a0,0x3a3
SEC("kprobe/blk_mq_dispatch_rq_list+0x3a0")
```

### 2. `xkernel/loader.py` — Load-Time Probe Optimization

**New functions:**

- `compile_single_bpf(bpf_c_path, bpf_dir)` — compiles a single BPF source file
- `check_kprobe_optimized(func_name, offset)` — reads `/sys/kernel/debug/kprobes/list` and checks for the `[OPTIMIZED]` flag
- `patch_bpf_sec_offset(bpf_c_path, func_name, old, new)` — rewrites the SEC annotation and `BPF_KPROBE` function name in the source file
- `try_jump_optimization(bpf_c_path, bpf_dir)` — main algorithm

**`try_jump_optimization` flow:**

```
1. Parse the BPF .c file; extract each kprobe's Candidates comment and current SEC offset.
2. For each kprobe with more than one candidate:
   a. Try each candidate offset in order:
      - Patch the SEC annotation → compile → bpftool loadall autoattach
      - Wait 0.5 s, then read /sys/kernel/debug/kprobes/list
      - If [OPTIMIZED]: select this offset, unload the test probe, move to next kprobe
      - Otherwise: unload, try the next candidate
   b. If no candidate is optimized, keep the original offset (first candidate)
3. Compile the final binary with the selected offsets.
```

Test probes are pinned under `/sys/fs/bpf/xkernel_jumpopt_test`, isolated from the production
load path. The source file is backed up before any patch and restored automatically on failure.

### 3. `xkernel/cli.py` — User Interface

A `--jump-opt` flag is added to `cmd_load()`. It takes effect after cs_artifact generation and
BPF compilation, but before kernel module insertion:

```
xkernel-tool load --jump-opt 0 1
```

Pipeline insertion point:

```
generate cs_artifact → compile BPF → [--jump-opt: probe optimization] → insmod → loadall → load CS
```

## Data Flow

```
              codegen                           loader (--jump-opt)
                │                                     │
  BB file ──→ candidate_offsets ──→ BPF .c file       │
                │                   (// Candidates)   │
                │                         │            │
                ├──→ scope_table          └──→ try each candidate ──→ patch SEC
                │    (Candidates col)           ↓                      ↓
                │                          bpftool load          check OPTIMIZED
                │                               ↓                      ↓
                │                          bpftool unload        accept / next
                │                               ↓
                │                          final compile ──→ production load
```

## Jump-Opt Eligibility Check

### Why the Kernel Needs These Two Conditions

When jump-optimizing a kprobe, the kernel overwrites the probe site with a 5-byte `jmp rel32`.
The overwritten bytes may span more than one instruction. The kernel must **relocate** those
instructions to an out-of-line trampoline and execute them there, which imposes two hard
constraints:

1. **Covered region ≥ 5 bytes.** If the probe-site instruction is shorter than 5 bytes, the
   kernel absorbs following instructions until it accumulates at least 5 bytes.
2. **No relative addressing in the covered region.** Relative jumps, calls, and RIP-relative
   operands encode offsets relative to the *original* instruction address. After relocation to
   the trampoline those offsets are wrong and cannot be safely fixed up.

Instruction encodings that block jump-opt:

| Opcode | Meaning |
|--------|---------|
| `e8 xx xx xx xx` | `CALL rel32` |
| `e9 xx xx xx xx` | `JMP rel32` |
| `eb xx` | `JMP rel8` |
| `7x xx` (70–7f) | `Jcc rel8` |
| `0f 8x xx xx xx xx` (0f 80–8f) | `Jcc rel32` |
| ASM contains `(%rip)` | RIP-relative memory operand |

### `check_jump_optimizable` Algorithm

```python
def check_jump_optimizable(all_insts: List[str], idx: int) -> Tuple[bool, str]:
    # Step 1: accumulate instructions from idx until total bytes >= 5
    covered, total = [], 0
    for j in range(idx, len(all_insts)):
        n = get_insn_byte_count(all_insts[j])
        covered.append(all_insts[j])
        total += n
        if total >= 5:
            break
    if total < 5:
        return False, f"only {total}B (need >=5)"

    # Step 2: check each covered instruction for relative addressing
    for line in covered:
        b0, b1 = first_byte, second_byte  # from hex tokens in the line
        if b0 == 'e8':                        return False, "CALL rel32 (e8)"
        if b0 in ('e9', 'eb'):               return False, f"JMP ({b0})"
        if 0x70 <= int(b0, 16) <= 0x7f:      return False, f"Jcc rel8 ({b0})"
        if b0 == '0f' and 0x80 <= int(b1,16) <= 0x8f:
                                              return False, f"Jcc rel32 (0f {b1})"
        if '(%rip)' in asm_text:             return False, "RIP-relative (%rip)"

    return True, f"{total}B, no relative addr"
```

`get_insn_byte_count` counts the hex tokens between `<addr>:` and the first tab on a BB file
line, giving the raw byte length of that instruction.

### Jump-Opt Status for All Test-Case Candidates

| Test case | Candidate | Offset | Bytes | Jump-opt | Reason |
|-----------|-----------|--------|-------|----------|--------|
| TC1 | SAVE shr | +0x217 | 3+2=5B | ✓ | extends into `cmp`, no relative |
| TC1 | #1★● cmp | +0x21a | 2+3=5B | ✓ | extends into `cmovb`, no relative |
| TC2 | #1★ mov | +0x406 | 3+5=8B | ✗ | extends into `call` (e8) |
| TC2 | #2● call | +0x409 | 5B | ✗ | opcode is e8 |
| TC3/BB1 | #1★ mov | +0x7c | 3+3=6B | ✓ | no relative |
| TC3/BB1 | #2  mov | +0x7f | 3+3=6B | ✓ | no relative |
| TC3/BB1 | #3● cmp | +0x82 | 3+7=10B | ✓ | `lea` uses rbp-relative (not RIP) |
| TC3/BB2 | #1★ cmova | +0x264 | 4+2=6B | ✓ | no relative |
| TC3/BB2 | #2  xor | +0x268 | 2+7=9B | ✗ | extends into `mov %gs:(%rip)` |
| TC3/BB2 | #3  mov_gs | +0x26a | 7B | ✗ | contains `(%rip)` |
| TC3/BB2 | #4  mov | +0x272 | 3+2=5B | ✓ | no relative |
| TC3/BB2 | #5● cmp | +0x275 | 2+3=5B | ✓ | no relative |
| TC3/BB3 | #1★ lea | +0x6bb | 4+3=7B | ✓ | no relative |
| TC3/BB3 | #2  mov | +0x6bf | 3+2=5B | ✓ | no relative |
| TC3/BB3 | #3● cmp | +0x6c2 | 2+3=5B | ✓ | `cmovge` is not Jcc |
| TC3/BB4 | #1★ mov | +0x53 | 5B | ✓ | exactly 5 bytes, no relative |
| TC3/BB4 | #2  lea | +0x58 | 4+5=9B | ✗ | extends into `call` (e8) |
| TC3/BB4 | #3● call | +0x5c | 5B | ✗ | opcode is e8 |
| TC4 | SAVE shr | +0x6a | 4+4=8B | ✓ | extends into `imul` (0f af ≠ Jcc) |
| TC4 | #1★● imul | +0x6e | 4+7=11B | ✓ | no relative |
| TC5/BB1 | #1★ mov | +0x57c | 3+5=8B | ✗ | extends into `call` (e8) |
| TC5/BB1 | #2● call | +0x57f | 5B | ✗ | opcode is e8 |
| TC5/BB2 | #1★ mov | +0x5c9 | 3+5=8B | ✗ | extends into `call` (e8) |
| TC5/BB2 | #2● call | +0x5cc | 5B | ✗ | opcode is e8 |

## Candidate Window Verification

| Test case | Function | Target reg | Candidate offsets | Window-end reason |
|-----------|----------|------------|-------------------|-------------------|
| TC1 | cubictcp_acked | %eax | `[0x21a]` | `cmp` reads eax immediately |
| TC2 | blk_mq_dispatch_rq_list | %esi | `[0x406, 0x409]` | `call` implicitly reads esi |
| TC3/BB1 | io_cqring_wait | %ecx | `[0x7c, 0x7f, 0x82]` | `cmp` reads ecx |
| TC3/BB2 | __do_sys_io_uring_enter | %eax | `[0x264, 0x268, 0x26a, 0x272, 0x275]` | `cmp` reads eax |
| TC3/BB3 | __do_sys_io_uring_enter | %eax | `[0x6bb, 0x6bf, 0x6c2]` | `cmp` reads eax |
| TC3/BB4 | io_run_task_work_sig | %ecx | `[0x53, 0x58, 0x5c]` | `call` implicitly reads ecx |
| TC4 | tcp_rack_detect_loss | %r15d | `[0x6e]` | `imul` reads r15d immediately |
| TC5/BB1 | __blk_mq_sched_dispatch | %esi | `[0x57c, 0x57f]` | `call` implicitly reads esi |
| TC5/BB2 | __blk_mq_sched_dispatch | %esi | `[0x5c9, 0x5cc]` | `call` implicitly reads esi |

## Usage

```bash
# Build (generates BPF files with candidate information)
./xkernel-tool build

# Inspect candidate offsets
grep "Candidates:" bpf/stubs/xtune_stub_*.bpf.c

# Load with jump optimization
./xkernel-tool load --jump-opt 0 1

# Verify optimization status
sudo cat /sys/kernel/debug/kprobes/list | grep OPTIMIZED

# Load without optimization (backward compatible)
./xkernel-tool load 0 1
```
