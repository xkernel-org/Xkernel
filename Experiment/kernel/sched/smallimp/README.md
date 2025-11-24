- Make sure your machine has more than one NUMA nodes:

```bash
numactl -H
```

- Config:

```bash
cat /proc/sys/kernel/numa_balancing
0
echo 1 | sudo tee /proc/sys/kernel/numa_balancing

cat  /proc/sys/kernel/numa_balancing_promote_rate_limit_MBps
65536
echo 64 | sudo tee /proc/sys/kernel/numa_balancing_promote_rate_limit_MBps
64

sudo cat /sys/kernel/debug/sched/numa_balancing/hot_threshold_ms
1000
echo 10  | sudo tee /sys/kernel/debug/sched/numa_balancing/hot_threshold_ms
10

sudo cat /sys/kernel/debug/sched/numa_balancing/scan_period_min_ms
100
```

- Install `stress-ng`:

```bash
sudo apt-get update
sudo apt install stress-ng
```

- Run with:

```bash
stress-ng --cpu $(nproc) --timeout 0 >/dev/null 2>&1 &

stress-ng --numa $(nproc) --vm $(nproc) --vm-bytes 1G \
          --vm-keep --timeout 60s
```