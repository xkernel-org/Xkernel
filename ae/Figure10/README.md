# Figure 10

Zswap shrinker latency under different `SHRINK_BATCH` values.

## Testbed

1 CloudLab machine with swap enabled.

## Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and `source ~/xk-py/bin/activate` before plotting.

```bash
bash install_zswap_min.sh           # build zswap_min benchmark
export KERNEL_DIR=~/linux-6.8.0     # kernel source for codegen
bash run.sh                         # ~20 minutes
python3 plot/plot.py                # → plot/figure10.pdf
```

### Estimated time

| Step                 | Time       |
|----------------------|------------|
| `install_zswap_min.sh` | ~30 sec  |
| `run.sh`             | ~20 min    |
| Total                | ~20 min    |

## Expected Results

The `SHRINK_BATCH` constant in `mm/shrinker.c` controls how many objects the
shrinker processes per batch (default 128). Xkernel tunes this value at runtime
and measures iteration latency in a memory-pressure workload (`zswap_min`).

Representative results on CloudLab (kernel 6.8.0-101-generic):

| SHRINK_BATCH | P50 (µs) | P90 (µs) | P99 (µs) | CPU Usage (%) |
|--------------|----------|----------|----------|---------------|
| 8            | ~480     | ~2,200   | ~7,800   | ~32%          |
| 16           | ~780     | ~3,800   | ~14,000  | ~38%          |
| 24           | ~1,050   | ~5,200   | ~19,000  | ~42%          |
| 28           | ~1,180   | ~5,900   | ~21,500  | ~44%          |
| 32           | ~1,320   | ~6,500   | ~24,000  | ~46%          |
| 64           | ~2,400   | ~12,000  | ~44,000  | ~55%          |
| **128** (default) | ~4,500 | ~22,000 | ~80,000 | ~65%       |

**Key takeaway:** Smaller `SHRINK_BATCH` values reduce tail latency (P99)
significantly — e.g., `SHRINK_BATCH=8` cuts P99 by ~10× compared to the
default 128 — at the cost of higher per-batch overhead (more frequent but
smaller batches). The CPU usage also decreases with smaller batch sizes.

> **Note:** Exact numbers may vary across runs and machines due to differences
> in hardware, memory pressure, and swap device performance. The key observation
> is the monotonic trend — smaller batch sizes consistently reduce latency.
