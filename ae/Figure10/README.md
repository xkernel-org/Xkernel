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
| 8            | 130,904  | 140,793  | 843,987  | 51%           |
| 16           | 130,742  | 140,956  | 864,219  | 51%           |
| 24           | 108,848  | 143,901  | 915,125  | 51%           |
| 28           | 91,922   | 139,672  | 1,026,346| 52%           |
| 32           | 91,660   | 133,475  | 1,134,766| 53%           |
| 64           | 89,010   | 113,628  | 1,170,472| 54%           |
| **128** (default) | 91,359 | 117,626 | 1,226,953 | 56%      |

**Key takeaway:** Smaller `SHRINK_BATCH` values reduce P99 tail latency —
e.g., `SHRINK_BATCH=8` achieves ~31% lower P99 compared to the default 128.
Meanwhile P50 latency stays comparable across values 28–128, meaning the median
case is largely unaffected. CPU usage decreases slightly with smaller batch sizes.

> **Note:** Exact numbers may vary across runs and machines due to differences
> in hardware, memory pressure, and swap device performance. The key observation
> is the monotonic trend — smaller batch sizes consistently reduce latency.
