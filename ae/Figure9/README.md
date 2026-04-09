# Figure 9: Softirq Impact on Real-Time Latency

Measures `cyclictest` scheduling latency on a CPU core saturated with softirq
processing (from iperf3 network traffic), sweeping `MAX_SOFTIRQ_RESTART` = {1, 5, 10, 15, 20}.

## Setup (two machines)

**Server** (192.168.6.1):

```bash
bash install_cyclictest.sh

# 1. Steer all NIC flows to CPU 3
sudo bash steer_flows.sh 3

# 2. Start iperf3 servers (3 instances)
iperf3 -s -p 5200 & iperf3 -s -p 5201 & iperf3 -s -p 5202 &
```

**Client(s)**:

```bash
bash client.sh 192.168.6.1
```

## Run Experiment (server)

```bash
bash run.sh 3              # results → results/figure9.csv
python plot/plot_9.py       # → plot/figure9.pdf
```

## Scripts

| Script | Where | Description |
|--------|-------|-------------|
| `install_cyclictest.sh` | Server | Install `cyclictest` (rt-tests) |
| `steer_flows.sh` | Server | Pin all NIC RX flows to one CPU |
| `client.sh` | Client | Launch 3×32 iperf3 flows (Net-APP) |
| `run.sh` | Server | Sweep MAX_SOFTIRQ_RESTART, collect latency + CPU |
| `tune_softirq_restart.sh` | Server | Build & load MAX_SOFTIRQ_RESTART tunable |
| `metric.sh` | Server | Dump per-CPU softirq counts |
