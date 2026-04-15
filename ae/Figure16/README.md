# Figure 16

**Figure 16** — kprobe trigger overhead on the io\_uring write path.

Measures the P50 latency slowdown caused by attaching a BPF kprobe to
`io_write()`, the kernel function called exactly once per io\_uring write SQE.
The benchmark writes 1 byte to `/dev/null` via io\_uring at controlled IOPS
rates, so actual I/O cost ≈ 0 and kprobe overhead dominates.

Three sweep modes compare the cost of different kprobe mechanisms:

| Mode | File prefix | Mechanism | Overhead |
|------|-------------|-----------|----------|
| Baseline | `base_*` | No kprobes | — |
| Jump-opt | `xk_*` | `io_write+0x6` `[OPTIMIZED]` (5-byte `jmp rel32`) | ~25 ns |
| INT3 | `xkint3_*` | `io_write+0x6` (optimization disabled) | ~115 ns |

## Prerequisites

```bash
# Install plotting environment (one-time)
bash Xkernel/plot_env.sh
source ~/xk-py/bin/activate

# Build KernelX (one-time)
sudo bash build.sh
```

## Quick Start

```bash
# 1. Install dependencies and build benchmark
bash install_bench.sh

# 2. Run the full experiment (baseline + xk + xkint3)
sudo bash run.sh

# 3. Plot results
python plot/plot.py                 # → plot/figure16.pdf
```

## Step-by-step

### 1. Install

```bash
bash install_bench.sh
```

Installs `liburing-dev`, `bpftrace`, and builds the io\_uring benchmark (`bin/bench`).

### 2. Run

`run.sh` automates the full experiment:

- **Baseline sweep**: io\_uring benchmark at 100K–3M IOPS, no kprobes
- **xk sweep**: Attach jump-optimized kprobe to `io_write+0x6`, repeat sweep
- **xkint3 sweep**: Disable kprobe optimization (`sysctl debug.kprobes_optimization=0`),
  repeat sweep with INT3 kprobe at the same offset
- Data saved to `data/` as `{base,xk,xkint3}_<delay>_<iops>.txt`

```bash
sudo bash run.sh

# Optional: customize app delay and thread count
sudo bash run.sh --app-delay 5 --threads 8
```

### 3. Plot

```bash
python plot/plot.py                 # auto-detect data/
python plot/plot.py path/to/data    # specific data directory
```

Produces `plot/figure16.pdf` — P50 latency slowdown (%) vs offered IOPS.

## Scripts

| Script | Description |
|--------|-------------|
| `install_bench.sh` | Install deps, build benchmark |
| `run.sh` | Sweep IOPS for baseline / xk / xkint3 |
| `plot/plot.py` | Plot slowdown vs offered IOPS |

## Kprobe Target

The probe is placed at `io_write+0x6`, a 5-byte `mov $0x18,%ecx` instruction
in the function prologue. This offset is chosen over `+0x0` because:

- `+0x0` (`nopl`) is the ftrace trampoline → kprobe uses `[FTRACE]` mechanism
- `+0x6` supports true jump optimization → kernel patches with `jmp rel32` → `[OPTIMIZED]`
