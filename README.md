# Xkernel

**Xkernel** (KernelX) implements *Scoped Indirect Execution* (SIE) for runtime tuning of hardcoded performance constants in the Linux kernel — without recompilation or reboot.

Paper: *Principled Performance Tunability in Operating System Kernels* ([arXiv 2512.12530](https://arxiv.org/abs/2512.12530))

## How It Works

Linux contains hundreds of performance constants (`BLK_MAX_REQUEST_COUNT=128`, `MAX_SOFTIRQ_RESTART=10`, etc.) baked into the binary at compile time. SIE modifies their effect at runtime through three steps:

1. **Binary Diff** — Recompile the kernel with modified constant values and diff the assembly to locate the *Critical Span* (CS): the instruction sequence where the constant enters the architectural state.
2. **Symbolic Execution** — Derive the compiler's transformation `IV = f(V)` (e.g., `IV = V`, `IV = V << 3`) by symbolically executing the three BB versions.
3. **BPF Kprobe Synthesis** — Attach a kprobe after the CS that overwrites the register/memory with the new value, effectively replacing the constant at runtime.

### Consistency Models

| Mode | Name | Behavior |
|------|------|----------|
| 0 | Immediate | Takes effect instantly |
| 1 | Per-task | Each thread transitions on next CS entry (stack walk check) |
| 2 | Global | `stop_machine` + stack scan ensures all threads exit CS before activation |

## Environment Setup

### Install the custom kernel

```shell
sudo bash install.sh
```

### Install dependencies

```shell
sudo apt-get install clang llvm pahole pkg-config libelf-dev -y
```

```shell
# Latest libbpf
git clone https://github.com/libbpf/libbpf.git && \
  pushd libbpf/src && make -j$(nproc) && sudo make install && \
  sudo cp ./*.so /usr/local/lib/ && sudo ldconfig && popd
```

### Build kernel modules

```shell
cd kernel && ./build.sh
```

## Quick Start

### 1. Define test cases

Edit `xkernel/testcases.py` to specify the constants to tune:

```python
Testcase(
    name="BLK_MQ_RESOURCE_DELAY",
    description="block/blk-mq.c resource delay",
    file="block/blk-mq.c",
    original="BLK_MQ_RESOURCE_DELAY\t3",
    modified=["BLK_MQ_RESOURCE_DELAY\t5", "BLK_MQ_RESOURCE_DELAY\t7"],
    values=(3, 5, 7),
)
```

Each test case provides three values `(V1, V2, V3)`. The pipeline recompiles the kernel twice (`V1→V2`, `V1→V3`), diffs the binary, and uses symbolic execution to derive the transformation relationship.

### 2. Build (full pipeline)

```shell
./xkernel-tool build
```

This runs the three-stage pipeline:
1. **gen.py** — Binary diff + Basic Block extraction → `xkernel/bb_cache/`
2. **codegen.py** — Symbolic execution + BPF code generation → `bpf/examples/my_policy_N.bpf.c`
3. **make** — Compile BPF programs → `.bpf.o`

Use `--skip-gen` to skip the (slow) diff/BB stage when only codegen or compilation is needed:

```shell
./xkernel-tool build --skip-gen
```

### 3. Load a constant

```shell
# Immediate mode
sudo ./xkernel-tool load 0 1

# Per-task consistency
sudo ./xkernel-tool load 1 2

# Global consistency (5s timeout)
sudo ./xkernel-tool load 2 3 5

# With jump optimization
sudo ./xkernel-tool load 0 1 --jump-opt
```

### 4. Check status

```shell
sudo ./xkernel-tool status
```

### 5. Unload

```shell
# Unload a specific ConstID
sudo ./xkernel-tool unload 1

# Unload everything
sudo ./xkernel-tool unload --all
```

## CLI Reference

```
Usage: xkernel-tool <command> [options]

Commands:
  build     Run the full pipeline (gen → codegen → compile)
  load      Load BPF kprobes for a single ConstID
  unload    Unload BPF kprobes (per-ConstID or all)
  status    Show runtime status of loaded ConstIDs
  table     Manage scope tables (list, query, delete, cs, ss)
  trace     Display kernel BPF trace logs

Options for 'build':
  --skip-gen    Skip gen.py (only run codegen + make)

Options for 'load':
  <MODE>        0=Immediate, 1=Per-task, 2=Global
  <ConstID>     ConstID number from the scope table
  [timeout]     Timeout in seconds for Mode 2 (default: 5)
  --jump-opt    Probe candidate offsets for 5-byte JMP optimization

Options for 'unload':
  <ConstID>     Unload a specific ConstID
  --all         Unload all active ConstIDs and kernel modules

Options for 'table':
  list                    List all scope table entries
  query [filters]         Query entries with filters
  delete [filters|--all]  Delete entries
  cs [--index N]          Show Critical Span entries
  ss [--index N]          Show Safe Span entries
```

## Project Structure

```
Xkernel/
├── bpf/
│   ├── xkernel.bpf.h              # BPF runtime (transition_done, cs_map, etc.)
│   ├── kfuncs.bpf.h               # kfunc declarations
│   ├── util.bpf.h                 # Register read/write macros (BPF_SET_EAX, etc.)
│   ├── cs_artifact.bpf.h          # Auto-generated: per-task CS handler
│   ├── Makefile
│   └── examples/
│       └── my_policy_N.bpf.c      # Auto-generated BPF kprobe programs
├── kernel/
│   ├── kfuncs/                     # xk-kfuncs.ko: exports kfuncs to BPF
│   ├── consistency/                # xk-consistency.ko: global transition coordinator
│   └── build.sh
├── xkernel/
│   ├── cli.py                      # xkernel-tool CLI
│   ├── diff.py                     # Binary diff engine
│   ├── gen.py                      # BB file generator (calls diff.py)
│   ├── codegen.py                  # Symbolic execution + BPF code generation
│   ├── solver.py                   # Linear relationship solver (V → IV)
│   ├── loader.py                   # BPF loading/unloading lifecycle
│   ├── table.py                    # Scope/CS/SS table management
│   ├── objdump_helper.py           # Function address resolution
│   ├── testcases.py                # Test case definitions
│   └── bb_cache/                   # Generated Basic Block files
├── docs/
│   ├── jump_optimization.md        # Jump optimization design
│   └── per_constid_lifecycle.md    # Per-ConstID lifecycle design
├── xkernel-tool                    # CLI entry point
├── build.sh                        # Full build script (deps + modules + BPF)
└── install.sh                      # Kernel installation
```

## Data Flow

```
testcases.py                    ← Define constants to tune
    │
    ▼
diff.py (×2 per testcase)      ← Recompile kernel, binary diff
    │
    ▼
gen.py                          ← Extract Basic Blocks → bb_cache/N_bb_v{1,2,3}.txt
    │
    ▼
codegen.py                      ← Symbolic execution → derive IV = f(V)
    ├── Generate bpf/examples/my_policy_N.bpf.c
    └── Write /dev/shm/xkernel/{scope_table, cs_table, cs_raw}
    │
    ▼
make -C bpf/                    ← Compile .bpf.c → .bpf.o
    │
    ▼
xkernel-tool load <mode> <N>   ← Attach kprobes, manage consistency
    ├── Resolve function addresses via /proc/kallsyms
    ├── Load xk-kfuncs.ko (if needed)
    ├── bpftool loadall → /sys/fs/bpf/xkernel/N/
    ├── Populate cs_map with Critical Span ranges
    └── [Mode 2] insmod xk-consistency.ko → wait → activate → rmmod
```

## Synthesis Types

The codegen automatically detects and handles three synthesis patterns:

| Type | Seed Instruction | Strategy |
|------|-----------------|----------|
| **Simple** | `mov $imm, %reg` | Single kprobe after seed: overwrite register |
| **Irreversible** | `shr`/`shl`/`imul`/`and` | Two kprobes: save original value before seed, apply new computation after |
| **Memory-store** | `movl $imm, disp(%reg)` | Single kprobe after store: rewrite memory via `bpf_probe_write_kernel` |

## Runtime State

```
/dev/shm/xkernel/
├── scope_table     ← ConstID → BPF file mapping, status
├── cs_table        ← Critical Span instruction sequences
├── cs_raw          ← Unresolved CS entries (function+offset)
├── cs              ← Resolved CS entries (function+address+offsets)
└── runtime_state   ← JSON: active ConstIDs, loaded modules

/sys/fs/bpf/xkernel/<ConstID>/
├── progs/          ← Pinned BPF programs
└── maps/           ← Pinned BPF maps (cs_map, task_storage, etc.)
```
