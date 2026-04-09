# Figure 9: Softirq Impact on Real-Time Latency

Measures `cyclictest` scheduling latency on a CPU core saturated with softirq
processing (from iperf3 network traffic), before and after tuning
`MAX_SOFTIRQ_RESTART` with KernelX.

## Setup (two machines)

**Server** (192.168.6.1):

```bash
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
sudo bash run.sh 3
```

This will:
1. Record baseline latency + mpstat + softirq counts (MAX_SOFTIRQ_RESTART=10)
2. Tune MAX_SOFTIRQ_RESTART=1 via KernelX
3. Record tuned latency + mpstat + softirq counts
4. Clean up

## Scripts

| Script | Where | Description |
|--------|-------|-------------|
| `steer_flows.sh` | Server | Pin all NIC RX flows to one CPU |
| `client.sh` | Client | Launch 3×32 iperf3 flows (Net-APP) |
| `run.sh` | Server | Full experiment: baseline → tune → compare |
| `tune_softirq_restart.sh` | Server | Build & load MAX_SOFTIRQ_RESTART tunable |
| `metric.sh` | Server | Dump per-CPU softirq counts |
