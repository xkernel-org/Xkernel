# Figure 12

**Figure 12** — Flow completion time (FCT) of different HyStart parameters
(perf-consts) under different RTTs running NGINX.

This experiment demonstrates KernelX's ability to tune TCP CUBIC perf-consts
at runtime with an **RTT-aware policy**. Two hardcoded constants in HyStart's
delay-based congestion detection are tuned simultaneously, but only for
high-RTT flows:

1. **Scaling factor (SF)**: Controls the delay threshold via `delay_min >> SF`
   - Default SF=3 → narrow threshold (exit slow-start early)
   - KernelX SF=1 → wider threshold (stay in slow-start longer)
   - **Only applied when `curr_rtt >= 80ms`** (RTT-aware X-tune policy)

2. **HYSTART_DELAY_MAX**: Upper bound for the delay threshold clamp
   - Default: 16ms → limits threshold even with high RTT
   - KernelX: 32ms → allows larger threshold at high RTT

The RTT-aware BPF policy reads the socket's current RTT (`bictcp.curr_rtt`)
and only activates the tuning for flows with RTT ≥ 80ms. Low-RTT flows
remain on the default parameters.

## Setup

This experiment requires **two machines** connected via a direct link:

| Role   | IP            | NIC          | Software              |
|--------|---------------|--------------|-----------------------|
| Server | 192.168.6.1   | ens1f1np1    | NGINX (ports 80+8080) |
| Client | 192.168.6.2   | ens1f1np1    | wrk2                  |

**Dual-port netem** simulates two RTT classes simultaneously:
- Port 80 → 20ms RTT (10ms delay each side)
- Port 8080 → 80ms RTT (40ms delay each side)
- 2Gbps rate limit on server for bandwidth bottleneck

Traffic is steered using a `prio` qdisc with `u32` filters by port number.

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

Installs NGINX on ports 80 and 8080, generates 100 files with a heavy-tailed
HD Photo distribution (10KB–100MB) at `/var/www/html/bench/`, sorted by size
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

# Load both tunables (SF=1 for RTT>=80ms, DELAY_MAX=32ms)
sudo bash tune_tcp_cubic.sh load

# Unload
sudo bash tune_tcp_cubic.sh unload
```

### 4. Run

`run.sh` automates the full experiment from the server:

1. Sets up dual-port netem (port 80→20ms, port 8080→80ms)
2. **Vanilla**: Runs two wrk2 clients simultaneously (one per port)
3. **Builds** HyStart tunables via KernelX (one-time)
4. **KernelX**: Loads tunables (RTT-aware), runs both wrk2 clients
5. **Cleanup**: Unloads tunables, clears netem

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
- **Adaptive SF (20ms)** / **Adaptive SF (80ms)**: KernelX with RTT-aware policy

## Experiment Parameters

| Parameter      | Value  | Description                                |
|----------------|--------|--------------------------------------------|
| `--duration`   | 60s    | wrk2 test duration per run (per port)      |
| `--rate`       | 800    | Target requests/sec (per port)             |
| `--threads`    | 4      | wrk2 client threads (per port)             |
| `--connections` | 200   | Concurrent connections (per port)          |
| Port 80        | 20ms   | Low-RTT class (netem 10ms each side)       |
| Port 8080      | 80ms   | High-RTT class (netem 40ms each side)      |
| Rate limit     | 2Gbps  | netem rate on server (per port)            |
| Files          | 100    | HD Photo distribution (10KB–100MB)         |
| Access pattern | Zipf   | α=1.2, deterministic per-thread seed       |

## Key Results

KernelX with RTT-aware policy reduces 80ms tail latency while leaving 20ms
flows unchanged:
- **80ms RTT**: ~14% P99.9, ~12% P99.99 FCT reduction
- **20ms RTT**: No change (policy does not fire for low-RTT flows)

The improvement targets the extreme tail (P99.9+) where large file transfers
on high-RTT paths benefit from staying in slow-start longer.

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
//
// RTT-aware policy: only applies SF=1 when bictcp.curr_rtt >= 80000us
```
