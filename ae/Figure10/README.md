# Figure 10

**Figure 10** — zswap shrinker latency under different `SHRINK_BATCH` values.

The `SHRINK_BATCH` constant in `mm/shrinker.c` controls how many objects the
shrinker processes per batch. The default is 128. This experiment measures how
changing that value affects iteration latency in a memory-pressure workload
(`zswap_min`), demonstrating KernelX's ability to tune this perf-const at runtime.

## Prerequisites

```bash
# Install plotting environment (one-time)
bash Xkernel/plot_env.sh
source ~/xk-py/bin/activate

# Make sure a swapfile exists
swapon --show

# Build KernelX (one-time)
sudo bash build.sh
```

## Quick Start

```bash
# 1. Install dependencies and build zswap_min benchmark
bash install_zswap_min.sh

# 2. Run the full experiment (baseline + tuned values)
sudo bash run.sh

# 3. Plot results
python plot/plot.py              # → plot/figure10.pdf
```

## Step-by-step

### 1. Install

```bash
bash install_zswap_min.sh
```

### 2. Tune (manual, optional)

```bash
# Set SHRINK_BATCH = 32
sudo bash tune_shrink_batch.sh 32

# Unload
sudo bash tune_shrink_batch.sh unload
```

### 3. Run

`run.sh` automates the full experiment:
- Configures zswap environment (enable zswap, shrinker, set pool limit, swappiness, etc.)
- Runs baseline (SHRINK_BATCH=128, kernel default)
- For each tuned value (8, 16, 24, 28, 32, 64): tunes via KernelX, runs benchmark, unloads
- Results saved to `results/<timestamp>/`

```bash
sudo bash run.sh
```

### 4. Plot

```bash
python plot/plot.py                          # auto-detect latest results
python plot/plot.py results/20251126-034820  # specific results dir
```

Produces `plot/figure10.pdf` — grouped bar chart of P50/P90/P99 iteration
latency (µs, log scale) for each SHRINK_BATCH value.
