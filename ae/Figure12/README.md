# Figure 12

**Figure 12** — Flow completion time (FCT) of different scaling factors
(perf-consts) under different RTTs running NGINX.

This experiment demonstrates KernelX's ability to tune TCP CUBIC perf-consts
at runtime. The HyStart delay-based congestion detection uses a hardcoded
scaling factor that controls slow-start exit sensitivity. KernelX dynamically
adjusts this scaling factor (SF=3 → SF=1), allowing flows to stay longer in
slow-start and achieve higher cwnd before transitioning to congestion avoidance.

## Setup

This experiment requires **two machines** connected via a direct link:

| Role   | IP            | NIC          | Software              |
|--------|---------------|--------------|-----------------------|
| Server | 192.168.6.1   | ens1f1np1    | NGINX, KernelX        |
| Client | 192.168.6.2   | ens1f1np1    | wrk2                  |

RTT and bandwidth are simulated using `tc netem` (delay + rate) on the server NIC.

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
distribution (10KB–100MB) at `/var/www/html/bench/`.

### 2. Install (Client)

```bash
bash install_nginx.sh client
```

Builds wrk2 from source and copies the Zipf access pattern Lua script.

### 3. Tune (manual, optional)

```bash
# Build tcp_cubic tunable (one-time)
sudo bash tune_tcp_cubic.sh build

# Set static SF=1
sudo bash tune_tcp_cubic.sh 1

# Load adaptive X-tune policy (SF=1)
sudo bash tune_tcp_cubic.sh adaptive

# Unload
sudo bash tune_tcp_cubic.sh unload
```

### 4. Run

`run.sh` automates the full experiment from the server:

1. **Vanilla (SF=3)**: Runs wrk2 with 20ms and 80ms netem delay + 1Gbps rate limit
2. **Builds** tcp_cubic tunable via KernelX (one-time)
3. **Adaptive SF**: Loads X-tune policy, runs wrk2 with 20ms and 80ms delay
4. **Cleanup**: Unloads tunable, clears netem

```bash
sudo bash run.sh
sudo bash run.sh --duration 120 --rate 100   # custom parameters
```

Results saved to `results/`.

### 5. Plot

```bash
python3 plot/plot.py                    # auto-detect results/
python3 plot/plot.py results/           # specific results dir
```

Produces `plot/figure12.pdf` — tail latency CDF comparing:
- **SF=3 (20ms)** / **SF=3 (80ms)**: Vanilla kernel with default scaling factor
- **Adaptive SF (20ms)** / **Adaptive SF (80ms)**: KernelX policy (SF=1)

## Experiment Parameters

| Parameter      | Value  | Description                          |
|----------------|--------|--------------------------------------|
| `--duration`   | 60s    | wrk2 test duration per run           |
| `--rate`       | 50     | Target requests/sec                  |
| `--threads`    | 4      | wrk2 client threads                  |
| `--connections` | 200   | Concurrent connections               |
| RTTs           | 20, 80 | Simulated round-trip times (ms)      |
| Rate limit     | 1Gbps  | netem rate (bottleneck bandwidth)    |
| Files          | 100    | HD Photo distribution (10KB–100MB)   |
| Access pattern | Zipf   | α=1.2, deterministic per-thread seed |

## Key Results

KernelX with SF=1 reduces tail latency compared to vanilla SF=3:
- **20ms RTT**: ~23% P99 FCT reduction
- **80ms RTT**: ~4-7% P99.9/P99.99 FCT reduction

The improvement is driven by HyStart's delay detection threshold: SF=1 gives
`clamp(delay_min/2, 4ms, 16ms)` vs SF=3's `clamp(delay_min/8, 4ms, 16ms)`.
The larger threshold allows one more doubling of cwnd during slow-start,
resulting in faster completion of large file transfers.

## TCP CUBIC Perf-Consts

The experiment tunes the `delay_min >> 3` scaling factor in `tcp_cubic.c`.
This controls HyStart's delay-based slow-start exit threshold:

- `HYSTART_DELAY_MAX` (16ms)
- `HYSTART_DELAY_MIN` (4ms)
- Scaling factor in `ca->delay_min >> SF` (default SF=3, XKernel sets SF=1)
