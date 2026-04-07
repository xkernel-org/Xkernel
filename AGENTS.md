# CLAUDE.md — KernelX Project Context

## What is this?

KernelX (Xkernel) enables runtime tuning of hardcoded performance constants in
the Linux kernel using Scoped Indirect Execution (SIE). It attaches eBPF kprobes
that overwrite register/memory state to simulate a different constant value,
without recompiling or rebooting the kernel.

## Quick Commands

```bash
# Build single tunable
./xkernel-tool build tunables/shrink_batch.toml

# Build all 9 tunables (clears tables first)
./xkernel-tool build --all

# Load ConstID 1 in immediate mode
sudo ./xkernel-tool load 0 1

# Check status
sudo ./xkernel-tool status

# Unload
sudo ./xkernel-tool unload 1

# Run tests
python -m pytest tests/ -v

# Check prerequisites
bash scripts/check_deps.sh

# Full build (deps + kernel modules + BPF)
sudo bash build.sh
```

## Repository Structure

```
src/cli.py       — CLI entry point (build/load/unload/status/table/trace)
src/config.py    — TOML config loader → TunableConfig dataclass
src/diff.py      — Kernel recompilation + binary diff
src/gen.py       — Basic Block extraction from diff output
src/codegen.py   — Symbolic execution engine + BPF code generation
src/loader.py    — BPF program loading lifecycle via bpftool
src/table.py     — Scope/CS/SS table CRUD operations
src/xtune.py     — X-tune stub generator (programmable policy plane)
bpf/             — BPF runtime headers + auto-generated stubs
kernel/          — Kernel modules (kfuncs, global consistency)
tunables/        — TOML tunable definitions
tests/           — Unit tests (pytest)
ae/              — Artifact evaluation experiment scripts
examples/        — Example X-tune policies from the paper
```

## Key Design Concepts

1. **Three-version compilation**: Recompile with V1→V2 and V1→V3 to understand
   how the compiler transforms the constant. The diff reveals "seed" instructions.

2. **Symbolic execution**: Execute x86 Basic Blocks symbolically to derive
   `IV = f(V)` where IV is the compiler's internal representation and V is the
   source value. This relationship is used to generate update code for any new V.

3. **Critical Span (CS)**: The instruction window where the constant enters
   architectural state. Specified as `[start, end]` offsets within a function.

4. **Safe Span (SS)**: Forward data dependency slice from CS. All instructions
   consuming constant-derived values. Transition is safe only when execution is
   outside all SSes.

5. **Consistency modes**: Immediate (mode 0), Per-task (mode 1, uses
   BPF_MAP_TYPE_TASK_STORAGE), Global (mode 2, uses stop_machine + refcounts).

## Important Files

- Entry point: `xkernel-tool` (calls `src/cli.py:main()`)
- Runtime state: `/dev/shm/xkernel/{scope_table,cs_raw,ss_raw,cs,ss,runtime_state}`
- BPF pins: `/sys/fs/bpf/xkernel/<ConstID>/`
- Kernel modules: `kernel/kfuncs/` (xk-kfuncs.ko), `kernel/consistency/` (xk-consistency.ko)

## Architecture Constraints

- Python 3.11+ (uses `tomllib` from stdlib)
- BPF compilation requires: clang, llvm, libbpf, bpftool, vmlinux.h
- Kernel modules require kernel headers for the running kernel
- Custom kernel (6.14.0-xkernel) needed for full functionality
- x86-64 only (symbolic executor handles AT&T syntax x86 instructions)
