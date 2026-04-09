# Figure 1

- **Figure 1(a)** — Throughput of FIO sequential read/write on HDD
- **Figure 1(b)** — Latency and CPU breakdown of RocksDB `multireadrandom` on NVMe SSD

## Prerequisites for plotting

```bash
bash Xkernel/plot_env.sh    # → font, matplotlib, etc.
source ~/xk-py/bin/activate
```

## Figure 1(a): FIO on HDD

Please run this script on Cloudlab c220g5.

```bash
bash install_fio.sh
bash ./run1a.sh
python plot/plot_1a.py      # → plot/figure1a.pdf
```

## Figure 1(b): RocksDB on NVMe SSD

Please run this script on Cloudlab c6620.

```bash
bash install_rocksdb.sh
bash ./run1b.sh
python plot/plot_1b.py      # → plot/figure1b.pdf
```
