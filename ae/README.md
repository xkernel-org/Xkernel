# KernelX Artifact Evaluation

This directory contains scripts to reproduce the experiments from the paper:
*Principled Performance Tunability in Operating System Kernels* (arXiv:2512.12530)

## Prerequisites

- Custom kernel `6.14.0-xkernel` installed and booted (see `install.sh`)
- All dependencies built (run `sudo bash build.sh` from repo root)
- Verify with: `./xkernel-tool doctor`

## Hardware Requirements

- x86-64 machine with ≥128GB RAM, ≥28 cores
- Two 800GB NVMe SSDs (Gen4) recommended for storage experiments
- 25 Gbps networking for TCP experiments (4-node cluster)

## Directory Structure

```
ae/
├── README.md                  <- This file
├── run_all.sh                 <- Master script: runs all experiments
├── common.sh                  <- Shared helpers (timing, logging, result collection)
├── exp1_blk_max_request.sh    <- Fig. 1: BLK_MAX_REQUEST_COUNT (FIO + RocksDB)
├── exp2_softirq.sh            <- Fig. 9: MAX_SOFTIRQ_RESTART cost-benefit
├── exp3_shrink_batch.sh       <- Fig. 10: SHRINK_BATCH write latency
├── exp4_numa_migration.sh     <- Fig. 11: NR_MAX_BATCHED_MIGRATION TLB
├── exp5_tcp_cubic_nginx.sh    <- Fig. 12: TCP CUBIC HyStart + NGINX
├── exp6_overhead.sh           <- Fig. 16: SIE overhead microbenchmark
├── exp7_transition.sh         <- Fig. 17-20: Policy-update + transition time
├── results/                   <- Raw results (generated)
└── expected/                  <- Reference results with acceptable ranges
```

## Quick Start

```bash
# Run all experiments (takes several hours)
sudo bash ae/run_all.sh

# Run a single experiment
sudo bash ae/exp3_shrink_batch.sh

# Check results against expected ranges
bash ae/check_results.sh
```

## Experiment Details

### Experiment 1: BLK_MAX_REQUEST_COUNT (Fig. 1)
- **What**: Tunes block I/O plug threshold across hardware devices
- **Workload**: FIO with 4KB requests; RocksDB multiread-random
- **Values**: 1, 8, 16, 32, 64, 128
- **Expected**: 7× read, 54× write improvement on HDD; 1.2× throughput on NVMe
- **Time**: ~30 min

### Experiment 2: MAX_SOFTIRQ_RESTART (Fig. 9)
- **What**: Cost-benefit tradeoff between tail latency and CPU utilization
- **Workload**: cyclictest (latency) + throughput workload on 4-node cluster
- **Values**: 1, 2, 5, 10, 20, 50
- **Expected**: 149 µs optimal tail latency at 22% CPU penalty
- **Time**: ~20 min

### Experiment 3: SHRINK_BATCH (Fig. 10)
- **What**: Memory reclamation batch size for zswap shrinker
- **Workload**: Sequential mmap writes with periodic overwrites
- **Values**: 8, 16, 24, 32, 64, 128
- **Expected**: Values ≤24 avoid thrashing; ≥128 causes large latency
- **Time**: ~15 min

### Experiment 4: NR_MAX_BATCHED_MIGRATION (Fig. 11)
- **What**: Page migration batch size across NUMA nodes
- **Workload**: Hot data touching + migration threads
- **Values**: 1, 4, 16, 64, 256, 512
- **Expected**: Small values reduce latency, increase TLB shootdowns
- **Time**: ~20 min

### Experiment 5: TCP CUBIC HyStart (Fig. 12)
- **What**: Collective tuning of 3 interdependent perf-consts
- **Workload**: NGINX web server with mixed 20ms/80ms RTT flows
- **Expected**: 81% FCT reduction at P99.99 for long-RTT flows
- **Time**: ~30 min (requires network setup)

### Experiment 6: SIE Overhead (Fig. 16)
- **What**: Runtime overhead of SIE kprobes
- **Workload**: io_uring async writes to /dev/null, varying IOPS
- **Expected**: <1% slowdown at 20µs/op; <15% at 0µs/op
- **Time**: ~15 min

### Experiment 7: Transition Time (Fig. 17-20)
- **What**: Policy-update time and transition latency
- **Sub-experiments**: Per-thread atomicity, side-effect safety, global consistency
- **Expected**: <542ms policy load; <10ms per-thread; <144ms global
- **Time**: ~25 min
