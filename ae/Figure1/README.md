# Figure 1

This directory reproduces **Figure 1** from the paper, which demonstrates the
impact of tuning `BLK_MAX_REQUEST_COUNT` on two different hardware platforms:

- **Figure 1(a)** — FIO sequential read/write on an HDD (CloudLab c220g5)
- **Figure 1(b)** — RocksDB `multireadrandom` on an NVMe SSD (CloudLab c6620)

## Prerequisites

Install the Python plotting environment (only needed once):

```bash
bash Xkernel/plot_env.sh
```

## Figure 1(a): FIO on HDD

**Machine**: CloudLab c220g5

1. Run the FIO benchmark:

   ```bash
   bash ./run1a.sh
   ```

2. Generate the plot:

   ```bash
   python plot/plot_1a.py
   ```

   Output: `plot/figure1a.pdf`

## Figure 1(b): RocksDB on NVMe SSD

**Machine**: CloudLab c6620

1. Install RocksDB (only needed once):

   ```bash
   bash install_rocksdb.sh
   ```

2. Run the RocksDB benchmark:

   ```bash
   bash ./run1b.sh
   ```

3. Generate the plot:

   ```bash
   python plot/plot_1b.py
   ```

   Output: `plot/figure1b.pdf`

## Output Files

After running the experiments, raw results are saved under `results/`:

| File | Description |
|------|-------------|
| `results/hdd_32_read.txt` | FIO read, BLK_MAX_REQUEST_COUNT=32 |
| `results/hdd_32_write.txt` | FIO write, BLK_MAX_REQUEST_COUNT=32 |
| `results/hdd_128_read.txt` | FIO read, BLK_MAX_REQUEST_COUNT=128 |
| `results/hdd_128_write.txt` | FIO write, BLK_MAX_REQUEST_COUNT=128 |
| `results/nvme_32.txt` | RocksDB multiread, BLK_MAX_REQUEST_COUNT=32 |
| `results/nvme_32_cpu.txt` | sar CPU usage during baseline run |
| `results/nvme_1.txt` | RocksDB multiread, BLK_MAX_REQUEST_COUNT=1 |
| `results/nvme_1_cpu.txt` | sar CPU usage during tuned run |
