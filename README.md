# Xkernel

## Dependencies of Xkernel

```shell
# Sometimes we find the built-in kernel is too new after upgrading to 25.04, and there is no corresponding dbgsym package.
# Thus, we pick 6.14.0-15-generic.
sudo apt update && sudo apt install linux-image-6.14.0-15-generic linux-headers-6.14.0-15-generic && sudo update-grub && sudo reboot

# For linux-image-$(uname -r)-dbgsym
echo "deb http://ddebs.ubuntu.com $(lsb_release -cs) main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list.d/ddebs.list
echo "deb http://ddebs.ubuntu.com $(lsb_release -cs)-updates main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list.d/ddebs.list

sudo apt install ubuntu-dbgsym-keyring && sudo apt update

sudo apt-get install clang llvm libbpf-dev pahole gdb libgflags-dev \
     linux-image-$(uname -r)-dbgsym -y

# [Optional] Download the source code of the kernel. Xkernel doesn't depend on it.
sudo apt-get install linux-source -y
pushd /usr/src/ && sudo tar -xvf linux-source-6.14.0.tar.bz2 && popd
```

## Workflow of Xkernel

### 0. Compile and load kfuncs to kernel
`make -j && sudo insmod kernel_module/kfuncs.ko`.

### 1. Determine the offset to attach

For most cases, we can leverage gdb to help use analyze the kernel source code and locate the target line directly. \
E.g.,
`python gdb_core.py hystart_update 434,435 -e`.

However, for some cases that gdb is not helpful, we should use objdump to dump all the instructions of the function. \
E.g.,
`python ./objdump.py --func blk_mq_delay_run_hw_queue`.

### 2. Write eBPF code

eBPF files should be placed in `bpf_kprobe/bpf/examples`.

E.g., we want to attach a kprobe to the function `blk_mq_delay_run_hw_queue` at the offset `0xbe`:
```c
SEC("kprobe/blk_mq_delay_run_hw_queue+0xbe")
int BPF_KPROBE(blk_mq_delay_run_hw_queue) {
     return 0;
}
```

E.g., we want to attach a kprobe to the start of the function `blk_mq_delay_run_hw_queue`.
```c
SEC("kprobe/blk_mq_delay_run_hw_queue")
int BPF_KPROBE(blk_mq_delay_run_hw_queue) {
     return 0;
}
```

E.g., we want to attach a kprobe to the end of the function `blk_mq_delay_run_hw_queue`.
```c
SEC("kretprobe/blk_mq_delay_run_hw_queue")
int BPF_KRETPROBE(blk_mq_delay_run_hw_queue) {
     return 0;
}
```

### 3. Load BPF programs

The loader will detect the function name and the offset automatically. \
E.g.,
`sudo ./kprobe_loader --files blk-mq.bpf.o`.

Multiple BPF files are also supported, separated by comma. \
E.g.,
`sudo ./kprobe_loader --files blk-mq.bpf.o,softirq.bpf.o`.

## Case Studies

Cases are summarized in [CaseStudy](CaseStudy/constant.md).

## Analyze Git History of Constant Changes

The `analyze_symbol_changes.py` script is a powerful tool for analyzing changes of kernel symbols across different kernel versions. It can track how constants, macros, and other symbols have evolved throughout the Linux kernel development history.

### Features

- **Multi-threaded Analysis**: Parallel processing for faster analysis across large version ranges
- **Flexible Symbol Input**: Support for single symbols, comma-separated lists, or symbols from files

### Basic Usage

```bash
# Analyze a single symbol
python analyze_symbol_changes.py SMC_TX_WORK_DELAY --kernel-path ~/linux --start-version v5.0 --end-version v5.2

# Analyze multiple symbols
python analyze_symbol_changes.py "SMC_TX_WORK_DELAY,NETDEV_TX_BUSY" --kernel-path ~/linux

# Use symbols from a file
python analyze_symbol_changes.py --symbols-file symbols.txt --kernel-path ~/linux
```

### Command Line Options
<details>
<summary>Click to expand: Command line options</summary>

```bash
python analyze_symbol_changes.py [SYMBOL] [OPTIONS]

Arguments:
  SYMBOL                    Symbol to search for (e.g., KFREE_DRAIN_JIFFIES). 
                           Can be comma-separated list of symbols.

Options:
  --symbols-file, -sf      File containing symbols to analyze (one symbol per line)
  --start-version, -s      Start version/tag for git range (default: v3.0)
  --end-version, -e        End version/tag for git range (default: v6.14)
  --kernel-path, -k        Path to kernel source code directory (required)
  --verbose, -v            Show verbose output including line numbers and context
  --very-verbose, -vv      Show very verbose output including full commit message
  --quiet, -q              Quiet mode: only show final analysis results
  --threads, -t            Number of threads for parallel processing (default: CPU count)
  --filter-duplicates, -d  Filter commits that only change line numbers but not actual values
```
</details>

### Input File Format
<details>
<summary>Click to expand: Input file format</summary>

The symbols file can contain symbols in the following formats:

```
# One symbol per line
SMC_TX_WORK_DELAY
NETDEV_TX_BUSY

# Symbol with specific file path
SMC_TX_WORK_DELAY,net/smc/smc_tx.c
NETDEV_TX_BUSY,include/linux/netdevice.h

# Comments are supported
# This is a comment
SMC_TX_WORK_DELAY
```
</details>

### Output Examples

<details>
<summary>Click to expand: Sample output from batch analysis</summary>

```bash
python3 analyze_symbol_changes.py -sf symbol.csv -k ~/linux -q -d
```

```
[1] IO_LOCAL_TW_DEFAULT_MAX
f46b9cdb | Wed Nov 20 [v6.12-rc4] | io_uring: limit local tw done | #define IO_LOCAL_TW_DEFAULT_MAX             20

[2] BLK_MQ_CPU_WORK_BATCH
506e931f | Wed May 7  [v3.15-rc1] | blk-mq: add basic round-robin of what CPU to queue workqueue work on | BLK_MQ_CPU_WORK_BATCH        = 8,

[3] BLK_MQ_BUDGET_DELAY
a0823421 | Mon Apr 20 [v5.7-rc2] | blk-mq: Rerun dispatching in the case of budget contention | #define BLK_MQ_BUDGET_DELAY     3           /* ms units */

[4] BLK_MQ_RESOURCE_DELAY
86ff7c2a | Tue Jan 30 [v4.15] | blk-mq: introduce BLK_STS_DEV_RESOURCE | #define BLK_MQ_RESOURCE_DELAY  3               /* ms units */

[5] THROTL_GRP_QUANTUM
e675df2a | Mon Sep 7  [v5.9-rc3] | blk-throttle: Define readable macros instead of static variables | #define THROTL_GRP_QUANTUM 8

[6] THROTL_QUANTUM
e675df2a | Mon Sep 7  [v5.9-rc3] | blk-throttle: Define readable macros instead of static variables | #define THROTL_QUANTUM 32

[7] MAX_GRO_SKBS
587652bb | Mon Nov 15 [v5.15] | net: gro: populate net/core/gro.c | #define MAX_GRO_SKBS 8

[8] MAX_PER_SOCKET_BUDGET
99b29a49 | Mon Oct 23 [v6.6-rc5] | xsk: Avoid starving the xsk further down the list | #define MAX_PER_SOCKET_BUDGET (TX_BATCH_SIZE)

[9] fits_capacity
60e17f5c | Tue Jun 4  [v5.3-rc1] | sched/fair: Introduce fits_capacity() | #define fits_capacity(cap, max)      ((cap) * 1280 < (max) * 1024)

[10] capacity_greater
4aed8aa4 | Wed Apr 7  [v5.12-rc2] | sched/fair: Introduce a CPU capacity comparison helper | #define capacity_greater(cap1, cap2) ((cap1) * 1024 > (cap2) * 1078)

[11] KFREE_DRAIN_JIFFIES
a35d1690 | Mon Aug 5  [v5.5-rc1] | rcu: Add basic support for kfree_rcu() batching | #define KFREE_DRAIN_JIFFIES (HZ / 50)
51824b78 | Thu Jun 30 [v6.0-rc1] | rcu/kvfree: Update KFREE_DRAIN_JIFFIES interval | #define KFREE_DRAIN_JIFFIES (5 * HZ)

[12] MAX_SOFTIRQ_TIME
c10d7367 | Thu Jan 10 [v3.8-rc1] | softirq: reduce latencies | #define MAX_SOFTIRQ_TIME  msecs_to_jiffies(2)

[13] MAX_SOFTIRQ_RESTART
34376a50 | Thu Jun 6  [v3.10-rc5] | Fix lockup related to stop_machine being stuck in __do_softirq. | #define MAX_SOFTIRQ_RESTART 10

[14] SMC_WR_BUF_CNT
f38ba179 | Mon Jan 9  [v4.10-rc3] | smc: work request (WR) base for use by LLC and CDC | #define SMC_WR_BUF_CNT 16      /* # of ctrl buffers per link */

[15] SMC_TX_WORK_DELAY
18e537cd | Thu Sep 21 [v4.14-rc1] | net/smc: introduce a delay | #define SMC_TX_WORK_DELAY      HZ
16297d14 | Tue Feb 12 [v5.0-rc5] | net/smc: no delay for free tx buffer wait | #define SMC_TX_WORK_DELAY        0
```
</details>




