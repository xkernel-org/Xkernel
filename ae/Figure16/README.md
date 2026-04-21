# Figure 16

Per-trigger overhead of jump-optimized kprobe on the `io_write()` path.

## Testbed

1 CloudLab c6620 machine.

## Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and `source ~/xk-py/bin/activate` before plotting.

```bash
bash install_bench.sh         # build io_uring bench (~5 sec)
sudo bash run.sh              # ~10 minutes
python3 plot/plot.py          # → plot/figure16.pdf
```

### Estimated time

| Step              | Time      |
|-------------------|-----------|
| `install_bench.sh`| ~5 sec    |
| `run.sh`          | ~10 min   |
| Total             | ~10 min   |

## Expected results

Sweeps offered IOPS from 100K to 2.9M with 4 app-side delay values
(0, 5, 15, 20 µs). Measures P50 latency slowdown from a jump-optimized
kprobe on `io_write+0x6`.

| App delay (µs) | Avg P50 slowdown |
|-----------------|-----------------|
| 0               | ~20–25%         |
| 5               | ~5–10%          |
| 15              | <1%             |
| 20              | <1%             |

**Key takeaway:** With ≥15 µs of application-side work between I/O submissions,
the kprobe overhead is <1%. Even at 0 µs delay (worst case — pure kprobe
overhead), slowdown is bounded to ~20–25% at the highest IOPS rates.
