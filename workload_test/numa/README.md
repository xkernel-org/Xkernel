## Run with cgroup

Adapted from https://github.com/ece-fast-lab/ASPLOS-2025-M5

Setup

```shell
sudo apt-get install cgroup-tools

sudo tee /etc/cgconfig.conf << 'EOF'
group app {
    cpuset {}
    memory {}
}
EOF
sudo cgconfigparser -l /etc/cgconfig.conf
```

Run

```shell
# Replace with your workload
export CMD='sleep 100'
bash cgroup-wrapper.sh
```

The current configuration is to limit memory to one node at the beginning,
wait for some time (10s) for the workload to initialize itself, remove the
limit and trigger migration.

## Run X with `NUMA_PERIOD_THRESHOLD` value from 1 to 10

```shell
export BENCH_NAME=test
bash run-1-10.sh
```
