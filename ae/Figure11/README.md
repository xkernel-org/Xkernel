# Figure 11

**Figure 11** — NUMA page migration probe latency under different
`NR_MAX_BATCHED_MIGRATION` values.

The `NR_MAX_BATCHED_MIGRATION` constant in `mm/migrate.c` controls the maximum
number of pages migrated in a single batch. The default is 512 (= HPAGE_PMD_NR).
This experiment measures how changing that value affects query latency in a
NUMA-migration-heavy workload, demonstrating KernelX's ability to tune this
perf-const at runtime.

## Prerequisites

```bash
# Install plotting environment (one-time)
bash Xkernel/plot_env.sh
source ~/xk-py/bin/activate

# Build KernelX (one-time)
sudo bash build.sh

# Requires 2+ NUMA nodes
numactl --hardware
```

## Quick Start

```bash
# 1. Install dependencies and build benchmark
bash install_benchmark.sh

# 2. Run the full experiment (baseline + tuned values, 10 repeats each)
sudo bash run.sh

# 3. Plot results
python plot/plot.py              # → plot/figure11.pdf
```

## Step-by-step

### 1. Install

```bash
bash install_benchmark.sh
```

Installs `build-essential`, `numactl`, `libnuma-dev` and compiles `src/benchmark.c`.

### 2. Tune (manual, optional)

```bash
# Set NR_MAX_BATCHED_MIGRATION = 32
sudo bash tune_nr_max_batched_migration.sh 32

# Unload
sudo bash tune_nr_max_batched_migration.sh unload
```

### 3. Run

`run.sh` automates the full experiment:
- Disables `numa_balancing` to prevent interference
- Uses high migration pressure config: 24 workers, 2 migration threads,
  rolling hot set, 8 GiB total, NUMA node 1 → 0
- Runs 10 repeats for each value (baseline 512, tuned: 32, 64, 128, 256, 1024)
- Summarizes results via `plot/summarize.py`
- Results saved to `results/<timestamp>/`

```bash
sudo bash run.sh
```

### 4. Plot

```bash
python plot/plot.py                          # auto-detect latest results
python plot/plot.py results/20251126-034820  # specific results dir
```

Produces `plot/figure11.pdf` — grouped bar chart of P50/P90/P95/P99 probe
latency (µs) for each NR_MAX_BATCHED_MIGRATION value.

## Benchmark Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `--pages` | 2097152 | 8 GiB total anonymous memory |
| `--workers` | 24 | Query threads |
| `--migrates` | 2 | Migration threads |
| `--src/--dst` | 1/0 | Migrate from NUMA node 1 to node 0 |
| `--batch` | 8192 | User-space collection cap per attempt |
| `--hot-frac` | 0.20 | 20% hot window |
| `--hot-prob` | 0.80 | 80% access probability for hot pages |
| `--hot-rotate` | 1 | Rotate hot window every 1 second |
| `--duration` | 30 | 30 seconds per run |
