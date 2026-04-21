# Figure 1

- **Figure 1(a)** — Throughput of FIO sequential read/write on HDD
- **Figure 1(b)** — Latency and CPU breakdown of RocksDB `multireadrandom` on NVMe SSD

## Figure 1(a): FIO on HDD

### Testbed

1 CloudLab c220g5 machine.

### Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and `source ~/xk-py/bin/activate` before plotting.

```bash
bash install_1a.sh
bash run1a.sh
python3 plot/plot_1a.py      # → plot/figure1a.pdf
```

## Figure 1(b): RocksDB on NVMe SSD

### Testbed

1 CloudLab c6620 machine.

### Steps

> **Note:** Run `bash plot_env.sh` (in the repo root) and `source ~/xk-py/bin/activate` before plotting.

```bash
bash install_1b.sh
bash run1b.sh
python3 plot/plot_1b.py      # → plot/figure1b.pdf
```
