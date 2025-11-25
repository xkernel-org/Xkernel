# Directory structure

```
├── bin
│   └── zswap_min               
├── Makefile
├── README.md
├── res                         # You can delete existing test results and retest again       
│   ├── 8.txt
│   ├── ...
│   └── 128.txt
├── scripts
│   ├── bpftrace                
│   │   ├── nr_to_scan.bt
│   │   └── q_l_trace.bt
│   ├── plot                    
│   │   ├── dt_us.py
│   │   └── io.py
│   ├── stress-ng_trigger.sh
│   └── zswap_min.sh
└── src
    └── zswap_min.c             
```

# Before starting experiments

- Make sure the swapfile exists and turn off the zram
```
$ swapon --show
# If it does not exist, please create a swapfile

$ sudo systemctl stop zramswap.service 2>/dev/null || true
```

- Turn on the zswap and shrinker:
```
$ echo 1 | sudo tee /sys/module/zswap/parameters/enabled
$ echo Y | sudo tee /sys/module/zswap/parameters/shrinker_enabled
```

- Lower the pool limit to make writeback more aggressive (default 20):
```
$ echo 5  | sudo tee /sys/module/zswap/parameters/max_pool_percent
```

- Turn on the debugfs to watch more parameters:
```
$ mount -t debugfs none /sys/kernel/debug 2>/dev/null || true
```

- Increase global swappiness:
```
$ sysctl -w vm.swappiness=180
```

- Turn off THP:
```
$ echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
$ echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag
```

- Make sure you are using the default zswap parameters:
```
$ echo zbud | sudo tee /sys/module/zswap/parameters/zpool        
$ echo lzo  | sudo tee /sys/module/zswap/parameters/compressor   
```

# Reproduce 

In short, zswap_min.c allocates a large buffer in anonymous memory and divides it into fixed-size blocks. It first performs a warmup to quickly fill caches like zswap with highly compressible data.Then it enters the main loop: it writes blocks of the current batch in burst order and revisits blocks that are reuse_dist blocks earlier (simulating near-future reuse).The duration of each iteration is recorded in microseconds.

## Quick Start

First, attach the Xkernel bpf program to the kernel:

```
$ sudo ./kprobe_loader --files shrink_batch.bpf.o
```

Using multiple terminals or tmux:

```
# View swapin/swapout counts 
$ vmstat 3

# Trace Q_5s/L_est information
$ sudo bpftrace scripts/bpftrace/q_l_trace.bt

# Run the test program using default config
$ bash scripts/zswap_min.sh
```


## Execution Script 

zswap_min.c provides several options for testing various data types in different scenarios. Please refer to the source code for details. 

Some important options include:

```
--total-mb <MB>: The total amount of anonymous memory allocated and tested, in MiB.

--block-pages <N>: The number of pages per block. The default is 128 (i.e., 512 KiB per block).

--reuse-dist <N>: The revisit distance (in blocks). While writing the current block in the main loop, the block N blocks earlier is read, simulating near-future reuse.

--loops <N>: The number of main loop iterations (each iteration writes a burst of blocks and revisits the corresponding blocks).

--burst <N>: The batch size (number of blocks) to be processed sequentially in each iteration.

--file </path/to/file>: Output the results to the specified file.
```

We've provided a script, `scripts/zswap_min.sh`, for one-click execution. Specifically, this script specifies memory limits (such as `MemoryHigh`), creates a cgroup execution environment, and passes `zswap_min` command-line parameters:

```
$ bash scripts/zswap_min.sh
```

The program's output can be sent to a file or stdout, depending on the command-line parameters. After the program completes, `time` will display the program's timing information in the terminal.

## Trace (bpftrace) 

We primarily use two bpftrace scripts `q_l_trace.bt` and `nr_to_scan.bt` to record the necessary information:

`q_l_trace.bt` tracks and records the following information, outputting it to the terminal every 5 seconds. Important information includes:

- Q_5s = wb_ok + exist: zswap writeback throughput, where wb_ok represents the number of entries successfully written back, and exist represents an invalid writeback if the return value == -EEXIST.

- L_est: L_est = L / calls of zswap_shrinker_count(), representing the average return value of each call to zswap_shrinker_count(), representing the approximate number of entries that can be reclaimed.

- zswap_hit / zswap_miss: Whether a read or write operation hits zswap.

`nr_to_scan.bt` tracks whether our Xkernel bpf program successfully attaches and returns the batch size used during shrinking.
