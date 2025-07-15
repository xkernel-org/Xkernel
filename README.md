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

## Text Poke Functionality

Xkernel provides a high-performance API to modify kernel instructions at runtime safely. The eBPF program will be loaded into kernel and executed in a single shot.

### 1. ONE_SHOT_ENV()

The `ONE_SHOT_ENV()` is used to define the environment for text_poke operations. It takes two parameters:
- **Instruction address**: The memory address of the instruction to be modified
- **Instruction size**: The size of the instruction in bytes

```c
ONE_SHOT_ENV(
    0xffffffffac78ae58, // instruction address
    3                   // instruction size
);
```

### 2. BPF Text Poke Functions

Xkernel provides several BPF helper functions for text_poke operations:

- **BPF_WRITE_INSN()**: Writes new instruction bytes to the target address
- **BPF_RESTORE_INSN()**: Restores the original instruction bytes
- **BPF_PRINT_INSN()**: Prints the current instruction bytes for debugging

#### BPF_ONESHOT_INIT and BPF_ONESHOT_EXIT

These are the main entry points for text_poke operations:

- **BPF_ONESHOT_INIT()**: The initialization function that runs when the program is loaded. This is where you perform the instruction modification.
- **BPF_ONESHOT_EXIT()**: The cleanup function that runs when the program is unloaded. This is where you restore the original instructions.

```c
BPF_ONESHOT_INIT(test_text_poke) {
    BPF_PRINT_INSN("Old instruction");
    
    unsigned char new_insn[] = {0x83, 0xf8, 0x0b};
    BPF_WRITE_INSN(new_insn);

    BPF_PRINT_INSN("New instruction");
    return 0;
}

BPF_ONESHOT_EXIT(test_text_poke) {
    BPF_RESTORE_INSN();
    BPF_PRINT_INSN("Restored instruction");
    return 0;
}
```

The output should be like this:
```
[Old instruction]insn: 83 f8 0a
[New instruction]insn: 83 f8 0b
[Restored instruction]insn: 83 f8 0a
```

### 3. Loading Text Poke Programs

To load a text_poke BPF program, use the `--one-shot` flag with the loader:

```bash
sudo ./kprobe_loader --files test_text_poke.bpf.o --one-shot
```

The `--one-shot` flag indicates that this is a text_poke program that will modify kernel instructions temporarily and restore them when the program exits.

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
python analyze_symbol_changes.py "SMC_TX_WORK_DELAY,MAX_GRO_SKBS" --kernel-path ~/linux

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
<summary>Click to expand: Summary of the output</summary>

```bash
python3 analyze_symbol_changes.py -sf symbol.csv -k ~/linux -q -d
```

```
[1] IO_LOCAL_TW_DEFAULT_MAX
f46b9cdb | Wed Nov 20 [v6.12-rc4] | io_uring: limit local tw done | #define IO_LOCAL_TW_DEFAULT_MAX             20

[2] BLK_MQ_CPU_WORK_BATCH
506e931f | Wed May 7  [v3.15-rc1] | blk-mq: add basic round-robin of what CPU to queue workqueue work on | BLK_MQ_CPU_WORK_BATCH        = 8,

[3] BLK_MQ_BUDGET_DELAY
a0823421 | Mon Apr 20 [v5.7-rc2] | blk-mq: Rerun dispatching in the case of budget contention | #define BLK_MQ_BUDGET_DELAY     3               /* ms units */

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

[16] MAX_SCAN_WINDOW
598f0ec0 | Mon Oct 7  [v3.12-rc4] | sched/numa: Set the scan rate proportional to the memory usage of the task being scanned | #define MAX_SCAN_WINDOW 2560

[17] NUMA_IMBALANCE_MIN
abeae76a | Fri Nov 20 [v5.10-rc1] | sched/numa: Rename nr_running and break out the magic number | #define NUMA_IMBALANCE_MIN 2

[18] NUMA_PERIOD_SLOTS
04bb2f94 | Mon Oct 7  [v3.12-rc4] | sched/numa: Adjust scan rate in task_numa_placement | #define NUMA_PERIOD_SLOTS 10

[19] NUMA_PERIOD_THRESHOLD
04bb2f94 | Mon Oct 7  [v3.12-rc4] | sched/numa: Adjust scan rate in task_numa_placement | #define NUMA_PERIOD_THRESHOLD 3
a22b4b01 | Mon Jun 23 [v3.16-rc1] | sched/numa: Change scan period code to match intent | #define NUMA_PERIOD_THRESHOLD 7

[20] DL_SCALE
332ac17e | Thu Nov 7  [v3.13-rc7] | sched/deadline: Add bandwidth management for SCHED_DEADLINE tasks | #define DL_SCALE (10)
97fb7a0a | Sat Mar 3  [v4.16-rc2] | sched: Clean up and harmonize the coding style of the scheduler code base | #define DL_SCALE                10

[21] LOAD_AVG_PERIOD
283e2ed3 | Tue Apr 11 [v4.11-rc6] | sched/fair: Move the PELT constants into a generated header | #define LOAD_AVG_PERIOD 32

[22] LOAD_AVG_MAX
283e2ed3 | Tue Apr 11 [v4.11-rc6] | sched/fair: Move the PELT constants into a generated header | #define LOAD_AVG_MAX 47742

[23] RR_TIMESLICE
45ebd394 | Wed Feb 20 [v3.8] | sched: Move RR_TIMESLICE from sysctl.h to rt.h | #define RR_TIMESLICE            (100 * HZ / 1000)

[24] MAX_MEAS
4e88ec4a | Tue Aug 11 [v5.9-rc1] | rcuperf: Change rcuperf to rcuscale | #define MAX_MEAS 10000

[25] MIN_MEAS
4e88ec4a | Tue Aug 11 [v5.9-rc1] | rcuperf: Change rcuperf to rcuscale | #define MIN_MEAS 100

[26] RCU_KTHREAD_MAX
4102adab | Tue Oct 8  [v3.12-rc1] | rcu: Move RCU-related source code to kernel/rcu directory | #define RCU_KTHREAD_MAX      4

[27] RCU_JIFFIES_TILL_FORCE_QS
4102adab | Tue Oct 8  [v3.12-rc1] | rcu: Move RCU-related source code to kernel/rcu directory | #define RCU_JIFFIES_TILL_FORCE_QS (1 + (HZ > 250) + (HZ > 500))

[28] WCI_MAX_ENTS
63638450 | Wed May 17 [v6.4-rc1] | workqueue: Report work funcs that trigger automatic CPU_INTENSIVE mechanism | #define WCI_MAX_ENTS 128

[29] BH_WORKER_RESTARTS
4cb1ef64 | Sun Feb 4  [v6.7] | workqueue: Implement BH workqueues to eventually replace tasklets | #define BH_WORKER_RESTARTS   10

[30] BH_WORKER_JIFFIES
4cb1ef64 | Sun Feb 4  [v6.7] | workqueue: Implement BH workqueues to eventually replace tasklets | #define BH_WORKER_JIFFIES    msecs_to_jiffies(2)

[31] XDP_BULK_QUEUE_SIZE
89653987 | Fri Nov 13 [v5.9] | net: xdp: Introduce bulking for xdp tx return path | #define XDP_BULK_QUEUE_SIZE 16

[32] MPTCP_SCHED_MAX
73c900aa | Mon May 13 [v6.9-rc7] | mptcp: add net.mptcp.available_schedulers | #define MPTCP_SCHED_MAX          128

[33] MPTCP_SUBFLOWS_MAX
740ebe35 | Mon Aug 21 [v6.5-rc6] | mptcp: add struct mptcp_sched_ops | #define MPTCP_SUBFLOWS_MAX       8

[34] TCP_RACK_RECOVERY_THRESH
1f255691 | Fri Nov 3  [v4.14-rc7] | tcp: higher throughput under reordering with adaptive RACK reordering wnd | #define TCP_RACK_RECOVERY_THRESH 16

[35] NVME_NVM_IOSQES
69cd27e2 | Mon Jun 6  [v4.7-rc2] | nvme.h: add NVM command set SQE/CQE size defines | #define NVME_NVM_IOSQES           6

[36] NVME_NVM_IOCQES
69cd27e2 | Mon Jun 6  [v4.7-rc2] | nvme.h: add NVM command set SQE/CQE size defines | #define NVME_NVM_IOCQES           4

[37] NVME_ADM_SQES
c1e0cc7e | Wed Aug 7  [v5.3-rc3] | nvme-pci: Add support for variable IO SQ element size | #define NVME_ADM_SQES       6

[38] MIN_THREADS
ac1b398d | Thu Apr 16 [v4.0] | kernel/fork.c: avoid division by zero | #define MIN_THREADS 20

[39] GRO_HASH_BUCKETS
07d78363 | Sun Jun 24 [v4.18-rc2] | net: Convert NAPI gro list into a small hash table. | #define GRO_HASH_BUCKETS      8

[40] SHRINK_BATCH
96f7b2b9 | Mon Sep 11 [v6.6-rc4] | mm: vmscan: move shrinker-related code into a separate file | #define SHRINK_BATCH 128
```
</details>

<details>
<summary>Click to expand: Detailed output</summary>

```bash
python3 analyze_symbol_changes.py -sf symbol.csv -k ~/linux -d -v
```

```
Analyzing 1 symbol(s): SMC_TX_WORK_DELAY
================================================================================
Found SMC_TX_WORK_DELAY definition in: net/smc/smc_tx.c

Symbol 1/1: SMC_TX_WORK_DELAY
------------------------------------------------------------
Analyzing SMC_TX_WORK_DELAY changes from v3.0 to v6.14...
Using kernel source path: /users/chenzj/linux
Using 56 threads for parallel processing
Filtering duplicate definitions (keeping earliest commit)
================================================================================
Commit 1/2 (Thread 23): 18e537cd58e8d6932719bfa79cb96a1fbc639199
Author: Ursula Braun
Date: Thu Sep 21 09:16:33 2017 +0200
Kernel Version: v4.14-rc1
Message: net/smc: introduce a delay
SMC_TX_WORK_DELAY definition (line 27):
  #define SMC_TX_WORK_DELAY     HZ
  Context:
        25: #include "smc_tx.h"
      26: 
>>>   27: #define SMC_TX_WORK_DELAY     HZ
      28: 
      29: /***************************** sndbuf producer *******************************/
--------------------------------------------------------------------------------

Commit 2/2 (Thread 31): 16297d143989e3f5acd75c1ca0a771b78aa12b46
Author: Karsten Graul
Date: Tue Feb 12 16:29:52 2019 +0100
Kernel Version: v5.0-rc5
Message: net/smc: no delay for free tx buffer wait
SMC_TX_WORK_DELAY definition (line 31):
  #define SMC_TX_WORK_DELAY     0
  Context:
        29: #include "smc_tx.h"
      30: 
>>>   31: #define SMC_TX_WORK_DELAY     0
      32: #define SMC_TX_CORK_DELAY     (HZ >> 2)       /* 250 ms */
      33: 
--------------------------------------------------------------------------------
```

</details>

<details>
<summary>Click to expand: Very detailed output (full commit message)</summary>

```bash
python3 analyze_symbol_changes.py SMC_TX_WORK_DELAY -k ~/linux -d -vv
```

```
Analyzing 1 symbol(s): SMC_TX_WORK_DELAY
================================================================================
Found SMC_TX_WORK_DELAY definition in: net/smc/smc_tx.c
Thread 3: No changes found in range v3.4..v3.6
Thread 1: No changes found in range v3.0..v3.2
Thread 16: No changes found in range v4.6..v4.7
Thread 13: No changes found in range v4.3..v4.4
Thread 2: No changes found in range v3.2..v3.4
Thread 23: Found 1 commits in range v4.13..v4.14
Thread 27: Found 1 commits in range v4.17..v4.18
Thread 29: No changes found in range v4.19..v4.20
Thread 17: No changes found in range v4.7..v4.8
Thread 12: No changes found in range v4.2..v4.3
Thread 39: No changes found in range v5.8..v5.9
Thread 20: No changes found in range v4.10..v4.11
Thread 28: No changes found in range v4.18..v4.19
Thread 30: No changes found in range v4.20..v5.0
Thread 54: No changes found in range v6.11..v6.12
Thread 31: Found 1 commits in range v5.0..v5.1
Thread 25: Found 1 commits in range v4.15..v4.16
Thread 55: No changes found in range v6.12..v6.13
Thread 34: No changes found in range v5.3..v5.4
Thread 24: No changes found in range v4.14..v4.15
Thread 22: No changes found in range v4.12..v4.13
Thread 56: No changes found in range v6.13..v6.14
Thread 41: No changes found in range v5.10..v5.11
Thread 4: No changes found in range v3.6..v3.8
Thread 50: No changes found in range v5.19..v6.0
Thread 15: No changes found in range v4.5..v4.6
Thread 53: No changes found in range v6.10..v6.11
Thread 5: No changes found in range v3.8..v3.10
Thread 45: No changes found in range v5.14..v5.15
Thread 37: No changes found in range v5.6..v5.7
Thread 33: No changes found in range v5.2..v5.3
Thread 47: No changes found in range v5.16..v5.17
Thread 26: No changes found in range v4.16..v4.17
Thread 19: No changes found in range v4.9..v4.10
Thread 8: No changes found in range v3.14..v3.16
Thread 6: No changes found in range v3.10..v3.12
Thread 32: No changes found in range v5.1..v5.2
Thread 36: No changes found in range v5.5..v5.6
Thread 44: No changes found in range v5.13..v5.14
Thread 49: No changes found in range v5.18..v5.19
Thread 43: No changes found in range v5.12..v5.13
Thread 11: No changes found in range v4.0..v4.2
Thread 48: No changes found in range v5.17..v5.18
Thread 38: No changes found in range v5.7..v5.8
Thread 7: No changes found in range v3.12..v3.14
Thread 42: No changes found in range v5.11..v5.12
Thread 40: Found 1 commits in range v5.9..v5.10
Thread 35: Found 1 commits in range v5.4..v5.5
Thread 21: No changes found in range v4.11..v4.12
Thread 9: No changes found in range v3.16..v3.18
Thread 10: No changes found in range v3.18..v4.0
Thread 14: No changes found in range v4.4..v4.5
Thread 51: No changes found in range v6.0..v6.1
Thread 46: No changes found in range v5.15..v5.16
Thread 18: No changes found in range v4.8..v4.9
Thread 52: No changes found in range v6.1..v6.10

Symbol 1/1: SMC_TX_WORK_DELAY
------------------------------------------------------------
Analyzing SMC_TX_WORK_DELAY changes from v3.0 to v6.14...
Using kernel source path: /users/chenzj/linux
Using 56 threads for parallel processing
Filtering duplicate definitions (keeping earliest commit)
================================================================================
Divided version range into 56 sub-ranges:
  Thread 1: v3.0..v3.2
  Thread 2: v3.2..v3.4
  Thread 3: v3.4..v3.6
  Thread 4: v3.6..v3.8
  Thread 5: v3.8..v3.10
  Thread 6: v3.10..v3.12
  Thread 7: v3.12..v3.14
  Thread 8: v3.14..v3.16
  Thread 9: v3.16..v3.18
  Thread 10: v3.18..v4.0
  Thread 11: v4.0..v4.2
  Thread 12: v4.2..v4.3
  Thread 13: v4.3..v4.4
  Thread 14: v4.4..v4.5
  Thread 15: v4.5..v4.6
  Thread 16: v4.6..v4.7
  Thread 17: v4.7..v4.8
  Thread 18: v4.8..v4.9
  Thread 19: v4.9..v4.10
  Thread 20: v4.10..v4.11
  Thread 21: v4.11..v4.12
  Thread 22: v4.12..v4.13
  Thread 23: v4.13..v4.14
  Thread 24: v4.14..v4.15
  Thread 25: v4.15..v4.16
  Thread 26: v4.16..v4.17
  Thread 27: v4.17..v4.18
  Thread 28: v4.18..v4.19
  Thread 29: v4.19..v4.20
  Thread 30: v4.20..v5.0
  Thread 31: v5.0..v5.1
  Thread 32: v5.1..v5.2
  Thread 33: v5.2..v5.3
  Thread 34: v5.3..v5.4
  Thread 35: v5.4..v5.5
  Thread 36: v5.5..v5.6
  Thread 37: v5.6..v5.7
  Thread 38: v5.7..v5.8
  Thread 39: v5.8..v5.9
  Thread 40: v5.9..v5.10
  Thread 41: v5.10..v5.11
  Thread 42: v5.11..v5.12
  Thread 43: v5.12..v5.13
  Thread 44: v5.13..v5.14
  Thread 45: v5.14..v5.15
  Thread 46: v5.15..v5.16
  Thread 47: v5.16..v5.17
  Thread 48: v5.17..v5.18
  Thread 49: v5.18..v5.19
  Thread 50: v5.19..v6.0
  Thread 51: v6.0..v6.1
  Thread 52: v6.1..v6.10
  Thread 53: v6.10..v6.11
  Thread 54: v6.11..v6.12
  Thread 55: v6.12..v6.13
  Thread 56: v6.13..v6.14

Thread True completed: v3.4..v3.6 (0 commits)
Thread True completed: v3.0..v3.2 (0 commits)
Thread True completed: v4.6..v4.7 (0 commits)
Thread True completed: v4.3..v4.4 (0 commits)
Thread True completed: v3.2..v3.4 (0 commits)
Thread True completed: v4.19..v4.20 (0 commits)
Thread True completed: v4.7..v4.8 (0 commits)
Thread True completed: v4.2..v4.3 (0 commits)
Thread True completed: v5.8..v5.9 (0 commits)
Thread True completed: v4.10..v4.11 (0 commits)
Thread True completed: v4.18..v4.19 (0 commits)
Thread True completed: v4.20..v5.0 (0 commits)
Thread True completed: v6.11..v6.12 (0 commits)
Thread True completed: v6.12..v6.13 (0 commits)
Thread True completed: v5.3..v5.4 (0 commits)
Thread True completed: v4.14..v4.15 (0 commits)
Thread True completed: v4.12..v4.13 (0 commits)
Thread True completed: v6.13..v6.14 (0 commits)
Thread True completed: v5.10..v5.11 (0 commits)
Thread True completed: v3.6..v3.8 (0 commits)
Thread True completed: v5.19..v6.0 (0 commits)
Thread True completed: v4.5..v4.6 (0 commits)
Thread True completed: v6.10..v6.11 (0 commits)
Thread True completed: v3.8..v3.10 (0 commits)
Thread True completed: v5.14..v5.15 (0 commits)
Thread True completed: v5.6..v5.7 (0 commits)
Thread True completed: v5.2..v5.3 (0 commits)
Thread True completed: v5.16..v5.17 (0 commits)
Thread True completed: v4.16..v4.17 (0 commits)
Thread True completed: v4.13..v4.14 (1 commits)
Thread True completed: v4.15..v4.16 (1 commits)
Thread True completed: v4.9..v4.10 (0 commits)
Thread True completed: v3.14..v3.16 (0 commits)
Thread True completed: v4.17..v4.18 (1 commits)
Thread True completed: v3.10..v3.12 (0 commits)
Thread True completed: v5.0..v5.1 (1 commits)
Thread True completed: v5.1..v5.2 (0 commits)
Thread True completed: v5.5..v5.6 (0 commits)
Thread True completed: v5.13..v5.14 (0 commits)
Thread True completed: v5.18..v5.19 (0 commits)
Thread True completed: v5.12..v5.13 (0 commits)
Thread True completed: v4.0..v4.2 (0 commits)
Thread True completed: v5.17..v5.18 (0 commits)
Thread True completed: v5.7..v5.8 (0 commits)
Thread True completed: v3.12..v3.14 (0 commits)
Thread True completed: v5.11..v5.12 (0 commits)
Thread True completed: v4.11..v4.12 (0 commits)
Thread True completed: v3.16..v3.18 (0 commits)
Thread True completed: v5.9..v5.10 (1 commits)
Thread True completed: v5.4..v5.5 (1 commits)
Thread True completed: v3.18..v4.0 (0 commits)
Thread True completed: v4.4..v4.5 (0 commits)
Thread True completed: v6.0..v6.1 (0 commits)
Thread True completed: v5.15..v5.16 (0 commits)
Thread True completed: v4.8..v4.9 (0 commits)
Thread True completed: v6.1..v6.10 (0 commits)
Keeping first occurrence of definition: #define SMC_TX_WORK_DELAY       HZ...
Filtering duplicate definition in commit 1a0a04c7a82c4c4667ab5a9660dc37f6d365d9d3 (same as 18e537cd58e8d6932719bfa79cb96a1fbc639199)
Filtering duplicate definition in commit 01d2f7e2cdd31becffafa0cb82809a5e36558ec0 (same as 18e537cd58e8d6932719bfa79cb96a1fbc639199)
Keeping first occurrence of definition: #define SMC_TX_WORK_DELAY       0...
Filtering duplicate definition in commit b290098092e4aeaa1712d3326bf5b64d2751c740 (same as 16297d143989e3f5acd75c1ca0a771b78aa12b46)
Filtering duplicate definition in commit 22ef473dbd66a5241b6cedc186abca5a3a4eb922 (same as 16297d143989e3f5acd75c1ca0a771b78aa12b46)

Analysis completed in 3.24 seconds
Total commits analyzed: 2
Filtered duplicate definitions: 2 unique definitions

Commit 1/2 (Thread 23): 18e537cd58e8d6932719bfa79cb96a1fbc639199
Author: Ursula Braun
Date: Thu Sep 21 09:16:33 2017 +0200
Kernel Version: v4.14-rc1
Message: net/smc: introduce a delay
Full commit message:
----------------------------------------
net/smc: introduce a delay

The number of outstanding work requests is limited. If all work
requests are in use, tx processing is postponed to another scheduling
of the tx worker. Switch to a delayed worker to have a gap for tx
completion queue events before the next retry.

Signed-off-by: Ursula Braun <ubraun@linux.vnet.ibm.com>
Signed-off-by: David S. Miller <davem@davemloft.net>
----------------------------------------

SMC_TX_WORK_DELAY definition:
  #define SMC_TX_WORK_DELAY     HZ
--------------------------------------------------------------------------------

Commit 2/2 (Thread 31): 16297d143989e3f5acd75c1ca0a771b78aa12b46
Author: Karsten Graul
Date: Tue Feb 12 16:29:52 2019 +0100
Kernel Version: v5.0-rc5
Message: net/smc: no delay for free tx buffer wait
Full commit message:
----------------------------------------
net/smc: no delay for free tx buffer wait

When no free transfer buffers are available then a work to call
smc_tx_work() is scheduled. Set the schedule delay to zero, because for
the out-of-buffers condition the work can start immediately and will
block in the called function smc_wr_tx_get_free_slot(), waiting for free
buffers.

Signed-off-by: Karsten Graul <kgraul@linux.ibm.com>
Signed-off-by: Ursula Braun <ubraun@linux.ibm.com>
Signed-off-by: David S. Miller <davem@davemloft.net>
----------------------------------------

SMC_TX_WORK_DELAY definition:
  #define SMC_TX_WORK_DELAY     0
--------------------------------------------------------------------------------
```
</details>




