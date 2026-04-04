# KernelX (Xkernel) — Copilot Instructions

## Project Overview

KernelX implements **Scoped Indirect Execution (SIE)** for runtime tuning of hardcoded
performance constants (perf-consts) in the Linux kernel without recompilation or reboot.

Paper: *Principled Performance Tunability in Operating System Kernels* (arXiv:2512.12530)

## Architecture

The system has a **build-time pipeline** and a **runtime system**:

### Build Pipeline (`xkernel-tool build`)
1. **Config** (`src/config.py`) — Loads tunable definitions from TOML files → `TunableConfig`
2. **Diff** (`src/diff.py`) — Recompiles kernel with modified values, diffs assembly
3. **Gen** (`src/gen.py`) — Extracts Basic Blocks (V1, V2, V3) → `bb_cache/`
4. **Codegen** (`src/codegen.py`) — Symbolic execution on x86 BBs → derives `IV = f(V)` → generates BPF stubs
5. **Compile** (`bpf/Makefile`) — Compiles `.bpf.c` → `.bpf.o`

### Runtime System (`xkernel-tool load/unload/status`)
- **Loader** (`src/loader.py`) — Loads BPF programs via `bpftool`, populates CS/SS maps
- **BPF Runtime** (`bpf/xkernel.bpf.h`) — Binary search on CS/SS maps, transition logic
- **Kernel Modules** (`kernel/`) — `xk-kfuncs.ko` (write access), `xk-consistency.ko` (global transitions)

### Key Abstractions
- **Perf-const**: A hardcoded performance constant in the kernel (e.g., `BLK_MAX_REQUEST_COUNT=32`)
- **Critical Span (CS)**: Instruction sequence where the constant enters architectural state
- **Safe Span (SS)**: Data dependency slice from CS; all instructions consuming constant-derived values
- **SIE Indirection**: `{location, update}` pair — kprobe at location overwrites state for new value
- **X-tune**: User-written eBPF policy that decides when/how to change a perf-const value
- **ConstID**: Unique integer identifying a perf-const in the Scope Table

### Consistency Modes
- **Mode 0 (Immediate)**: Kprobe fires, overwrites state; no coordination
- **Mode 1 (Per-task)**: Guard/unguard kprobes at SS boundaries; per-task BPF storage
- **Mode 2 (Global)**: `stop_machine` + refcount; all threads must exit SS

## Code Conventions

- Python 3.11+, no external dependencies for core pipeline
- BPF code uses libbpf CO-RE style with `vmlinux.h`
- Kernel modules are GPL-licensed C
- CLI is in `src/cli.py`, entry point is `xkernel-tool` (shim script at repo root)
- Runtime state stored at `/dev/shm/xkernel/` (scope_table, cs_raw, ss_raw, etc.)
- BPF programs pinned at `/sys/fs/bpf/xkernel/<ConstID>/`

## Build & Test Commands

```bash
# Install custom kernel (one-time)
sudo bash install.sh

# Build everything (deps + kernel modules + BPF)
sudo bash build.sh

# Build single tunable
./xkernel-tool build tunables/shrink_batch.toml

# Build all tunables
./xkernel-tool build --all

# Run unit tests
python -m pytest tests/ -v

# Load/unload
sudo ./xkernel-tool load 0 1          # Immediate mode, ConstID 1
sudo ./xkernel-tool unload 1
sudo ./xkernel-tool status
```

## File Layout

- `src/` — Core Python pipeline (cli, config, diff, gen, codegen, loader, table, xtune)
- `bpf/` — BPF headers, Makefile, auto-generated stubs in `bpf/stubs/`
- `kernel/` — Kernel modules (kfuncs, consistency)
- `tunables/` — TOML config files defining perf-consts
- `tests/` — Unit tests (pytest)
- `ae/` — Artifact evaluation scripts
- `examples/` — Example X-tune policies from the paper
- `docs/` — Design docs, quickstart, guides
- `legacy/` — Old code, reference implementations, evaluation tools

## Important Notes

- The symbolic executor (`codegen.py`) handles AT&T syntax x86 assembly
- Three BB versions (V1, V2, V3) are needed to derive the IV↔V mapping
- The `scope_table` is TSV at `/dev/shm/xkernel/scope_table`
- BPF stubs follow naming: `xtune_stub_<ConstID>.bpf.c`
- Jump optimization requires 5-byte instruction window (see `docs/jump_optimization.md`)
