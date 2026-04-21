# Figure 9

# Testbed

2 CloudLab xl170 machines. Configure IPs as 192.168.6.1 (server) and 192.168.6.2 (client).

# Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and `source ~/xk-py/bin/activate` before plotting.

All commands are run on the **server** (192.168.6.1):

```bash
bash ../setup_ssh.sh                # one-time SSH key setup
bash install_cyclictest.sh          # installs server + client deps
bash run.sh 3                       # results → results/figure9.csv
python3 plot/plot.py                # → plot/figure9.pdf
```

# Expected Results

The experiment sweeps `MAX_SOFTIRQ_RESTART` over {1, 5, 10, 15, 20} with 2 repetitions each, measuring cyclictest tail/average latency and softirq CPU utilization on CPU 3.

| MAX_SOFTIRQ_RESTART | Worst Latency (µs) | Avg Latency (µs) | Softirq CPU % |
|---------------------|---------------------|-------------------|----------------|
| 1                   | 248 – 262           | 28 – 29           | ~89%           |
| 5                   | 457 – 571           | ~30               | ~79%           |
| 10 (default)        | 688 – 732           | ~31               | ~77%           |
| 15                  | 876 – 952           | 32 – 42           | 71 – 79%       |
| 20                  | 1203 – 2050         | 32 – 50           | 68 – 80%       |

**Trend:** Lower `MAX_SOFTIRQ_RESTART` values yield lower tail latency at the cost of higher softirq CPU usage. This demonstrates the latency–throughput tradeoff that XKernel can tune at runtime without recompilation or reboot.

> **Note:** Exact numbers may vary across runs and machines due to differences in hardware, system load, and network conditions. The key observation is the monotonic trend — lower values consistently reduce tail latency while increasing CPU overhead.
