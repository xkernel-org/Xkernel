# Figure 12

**Figure 12** — Flow completion time (FCT) of different HyStart parameters
(perf-consts) under different RTTs running NGINX.

This experiment demonstrates KernelX's ability to tune TCP CUBIC perf-consts
at runtime. Two hardcoded constants in HyStart's delay-based congestion
detection are tuned simultaneously:

1. **Scaling factor (SF)**: Controls the delay threshold via `delay_min >> SF`
   - Default SF=3 → narrow threshold (exit slow-start early)
   - KernelX SF=1 → wider threshold (stay in slow-start longer)

2. **HYSTART_DELAY_MAX**: Upper bound for the delay threshold clamp
   - Default: 16ms → limits threshold even with high RTT
   - KernelX: 32ms → allows larger threshold at high RTT

Together, these changes allow TCP flows to achieve higher cwnd during
slow-start before transitioning to congestion avoidance, reducing tail
latency for large file transfers.

## Setup

This experiment requires **two machines** connected via a direct link:

| Role   | IP            | NIC          | Software              |
|--------|---------------|--------------|-----------------------|
| Server | 192.168.6.1   | ens1f1np1    | NGINX, KernelX        |
| Client | 192.168.6.2   | ens1f1np1    | wrk2                  |

RTT and bandwidth are simulated using `tc netem` on both sides: half-RTT delay
on server + client, and a 2Gbps rate limit on the server for bandwidth bottleneck.

## Prerequisites

```bash
# Build KernelX (one-time, on server)
sudo bash build.sh

# Install plotting dependencies
sudo apt-get install python3-matplotlib python3-seaborn python3-numpy
```

## Quick Start

```bash
# 1. Install NGINX + workload on server
bash install_nginx.sh server

# 2. Install wrk2 on client
bash install_nginx.sh client

# 3. Run the full experiment (from server)
sudo bash run.sh

# 4. Plot results
python3 plot/plot.py              # → plot/figure12.pdf
```

## Step-by-step

### 1. Install (Server)

```bash
bash install_nginx.sh server
```

Installs NGINX, generates 100 files with a heavy-tailed HD Photo
distribution (10KB–100MB) at `/var/www/html/bench/`, sorted by size
(file_1 = smallest, so Zipf access concentrates on small files).

### 2. Install (Client)

```bash
bash install_nginx.sh client
```

Builds wrk2 from source and copies the Zipf access pattern Lua script.

### 3. Tune (manual, optional)

```bash
# Build both HyStart tunables (one-time)
sudo bash tune_tcp_cubic.sh build

# Load both tunables (SF=1, DELAY_MAX=32ms)
sudo bash tune_tcp_cubic.sh load

# Unload
sudo bash tune_tcp_cubic.sh unload
```

### 4. Run

`run.sh` automates the full experiment from the server:

1. **Vanilla**: Runs wrk2 with 20ms and 80ms netem delay (symmetric) + 2Gbps rate limit
2. **Builds** HyStart tunables via KernelX (one-time)
3. **KernelX**: Loads both tunables, runs wrk2 with 20ms and 80ms delay
4. **Cleanup**: Unloads tunables, clears netem

```bash
sudo bash run.sh
sudo bash run.sh --duration 120 --rate 3000   # custom parameters
```

Results saved to `results/`.

### 5. Plot

```bash
python3 plot/plot.py                    # auto-detect results/
python3 plot/plot.py results/           # specific results dir
```

Produces `plot/figure12.pdf` — tail latency CDF comparing:
- **SF=3 (20ms)** / **SF=3 (80ms)**: Vanilla kernel with default HyStart
- **Adaptive SF (20ms)** / **Adaptive SF (80ms)**: KernelX tuned HyStart

## Experiment Parameters

| Parameter      | Value  | Description                                |
|----------------|--------|--------------------------------------------|
| `--duration`   | 60s    | wrk2 test duration per run                 |
| `--rate`       | 800    | Target requests/sec                        |
| `--threads`    | 4      | wrk2 client threads                        |
| `--connections` | 200   | Concurrent connections                     |
| RTTs           | 20, 80 | Simulated round-trip times (ms)            |
| Rate limit     | 2Gbps  | netem rate on server (bottleneck bandwidth)|
| Delay          | sym.   | Half-RTT netem delay on each side          |
| Files          | 100    | HD Photo distribution (10KB–100MB)         |
| Access pattern | Zipf   | α=1.2, deterministic per-thread seed       |

## Key Results

KernelX with SF=1 + DELAY_MAX=32ms reduces tail latency compared to vanilla:
- **20ms RTT**: ~12% P99.9 FCT reduction
- **80ms RTT**: ~13% P99.9, ~15% P99.99 FCT reduction

The improvement is most pronounced at the extreme tail (P99.9+) where large
file transfers dominate. These flows benefit from staying in slow-start longer,
achieving a higher cwnd before entering congestion avoidance.

## TCP CUBIC Perf-Consts

The experiment tunes two constants in `hystart_update()` (tcp_cubic.c):

```c
// HyStart delay detection threshold:
//   threshold = clamp(delay_min >> SF, HYSTART_DELAY_MIN, HYSTART_DELAY_MAX)
//
// Vanilla: SF=3, DELAY_MAX=16ms → threshold = clamp(delay_min/8, 4ms, 16ms)
// KernelX: SF=1, DELAY_MAX=32ms → threshold = clamp(delay_min/2, 4ms, 32ms)
//
// At 80ms RTT: vanilla threshold=10ms, KernelX threshold=32ms (3.2x wider)
```
