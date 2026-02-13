# Xkernel

## Environment Setup

#### Install Linux kernel 6.14.

`sudo bash install.sh`

#### Install dependencies.

`sudo apt-get install clang llvm pahole pkg-config libelf-dev -y`

```shell
# Latest version of libbpf.
git clone https://github.com/libbpf/libbpf.git && pushd libbpf/src && make -j$(nproc) && sudo make install && sudo cp ./*.so /usr/local/lib/ && sudo ldconfig && popd
```

## Quick Start

### 0. Compile kernel modules
```
cd kernel && ./build.sh
```

### 1. Use binary diff to locate target instructions

See examples in `xkernel/tools/check_assembly_diff_examples.csv`.

```shell
# Example
sudo python xkernel/diff.py -f block/blk-mq.c -s "BLK_MAX_REQUEST_COUNT" "128" --lines 1371,1372
# The output should be like this:
-    81e5:      83 e0 e0  and    $0xffffffe0,%eax /users/chenzj/linux-6.14.0-xkernel/block/blk-mq.c:1371
-    81e8:      83 c0 40  add    $0x40,%eax       /users/chenzj/linux-6.14.0-xkernel/block/blk-mq.c:1371
```

### 2. Determine the offset to attach

Note that the function should not be inlined and can be found in `/proc/kallsyms`.

```shell
# Example
python xkernel/objdump_helper.py --func blk_add_rq_to_plug |grep -w 'add    $0x40,%eax' -C 1
# The ouput should be like this:
(+0xc5)ffffffff8dff9bf5:        83 e0 e0                and    $0xffffffe0,%eax
(+0xc8)ffffffff8dff9bf8:        83 c0 40                add    $0x40,%eax
(+0xcb)ffffffff8dff9bfb:        66 41 39 c6             cmp    %ax,%r14w
```

### 3. Write eBPF code

eBPF files should be placed in `bpf/examples`.
```c
// blk-mq.bpf.c
// SPDX-License-Identifier: GPL-2.0
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "xkernel.bpf.h"

// (+0xcb)ffffffff8dff9bfb:        66 41 39 c6             cmp    %ax,%r14w
SEC("kprobe/blk_add_rq_to_plug+0xcb")
int BPF_KPROBE(blk_add_rq_to_plug_0xcb) {

    if (!transition_done()) return 0;

    BPF_SET_EAX(ctx, 128);
    return 0;
}
```

Compile the eBPF programs.
```shell
cd bpf && make -j`nproc`
```
### 4. Consistency Span
Manually write the consistency span in the `/dev/shm/xkernel/cs` file or use auto-generation tool (TODO).

Each line describes a consistency span with the following format:
```
ksys_mmap_pgoff,0xffffffffbb2354a0,0x43,0x6c
```
- ksys_mmap_pgoff: function name
- 0xffffffffbb2354a0: the address of the function
- 0x43: the start offset of the function
- 0x6c: the end offset of the function

### 5. Load BPF programs
```shell
# Immediately enable the BPF Kprobes.
./xkernel-tool load 0 bpf/examples/blk-mq.bpf.o,bpf/examples/mmap.bpf.o

# Use per-task consistency model.
./xkernel-tool load 1 bpf/examples/blk-mq.bpf.o

# Use global consistency model and set timeout to 3 seconds.
./xkernel-tool load 2 bpf/examples/blk-mq.bpf.o 3
```

### 6. Unload all BPF programs
```shell
./xkernel-tool unload
```

### xkernel-tool

```shell
Usage: ./xkernel-tool <command> [options]

Commands:
  build     Generate BPF code from tests and compile
  load      Load BPF kprobes for specified ConstIDs or files
  unload    Unload all loaded BPF kprobes
  table     Manage scope tables (list, query, delete, cs, ss)
  trace     Trace the kernel logs

Options for 'build':
  --skip-gen    Skip running gen.py (only run codegen.py and make)

Options for 'load':
  <MODE>        0=Immediate, 1=Per-task, 2=Global
  <IDs/files>   ConstIDs (e.g., 1,2) or BPF file paths
  [timeout]     Optional timeout in seconds (for Mode 2)

Options for 'table':
  list                    List all scope table entries
  query [filters]         Query entries
  delete [filters|--all]  Delete entries
  cs [--index N]          Show Critical Span entries
  ss [--index N]          Show Symbolic State entries
```

### Example outputs of different consistency models

#### Global consistency model:
```shell
[107775.520824] Xkernel consistency module loaded
[107775.520829] Global consistency model is enabled
[107775.994777] stop_machine overhead: 46 us
[107775.994820] [Target Functions] [ksys_mmap_pgoff] at 0xffffffffbb2354a0 with span [0x43, 0x6c]
[107775.996365] Function ksys_mmap_pgoff[0x43, 0x6c] found in stack trace for task [test 0/149514]
[107775.996370] Stack trace for task [test 0]:
[107775.996372]   [0] vm_mmap_pgoff+0xc0/0x1a0
[107775.996377]   [1] ksys_mmap_pgoff+0x4a/0x270
[107775.996381]   [2] __x64_sys_mmap+0x33/0x70
[107775.996385]   [3] x64_sys_call+0x1fce/0x25a0
[107775.996388]   [4] do_syscall_64+0x7f/0x180
[107775.996393]   [5] entry_SYSCALL_64_after_hwframe+0x78/0x80
[107775.996397] Function ksys_mmap_pgoff[0x43, 0x6c] found in stack trace for task [test 2/149516]
[107775.996399] Stack trace for task [test 2]:
[107775.996400]   [0] vm_mmap_pgoff+0xc0/0x1a0
[107775.996403]   [1] ksys_mmap_pgoff+0x4a/0x270
[107775.996405]   [2] __x64_sys_mmap+0x33/0x70
[107775.996408]   [3] x64_sys_call+0x1fce/0x25a0
[107775.996410]   [4] do_syscall_64+0x7f/0x180
[107775.996412]   [5] entry_SYSCALL_64_after_hwframe+0x78/0x80
[107775.996415] Function ksys_mmap_pgoff[0x43, 0x6c] found in stack trace for task [test 3/149517]
[107775.996417] Stack trace for task [test 3]:
[107775.996418]   [0] vm_mmap_pgoff+0xc0/0x1a0
[107775.996420]   [1] ksys_mmap_pgoff+0x4a/0x270
[107775.996423]   [2] __x64_sys_mmap+0x33/0x70
[107775.996425]   [3] x64_sys_call+0x1fce/0x25a0
[107775.996427]   [4] do_syscall_64+0x7f/0x180
[107775.996429]   [5] entry_SYSCALL_64_after_hwframe+0x78/0x80
[107775.996433] Function ksys_mmap_pgoff[0x43, 0x6c] found in stack trace for task [test 5/149519]
[107775.996434] Stack trace for task [test 5]:
[107775.996435]   [0] vm_mmap_pgoff+0xc0/0x1a0
[107775.996437]   [1] ksys_mmap_pgoff+0x4a/0x270
[107775.996440]   [2] __x64_sys_mmap+0x33/0x70
[107775.996442]   [3] x64_sys_call+0x1fce/0x25a0
[107775.996444]   [4] do_syscall_64+0x7f/0x180
[107775.996447]   [5] entry_SYSCALL_64_after_hwframe+0x78/0x80
[107775.996463] Initial refcount: 4
[107775.996484] [Transition] Waiting for transition to be done or failed
[107776.015601] [Transition] Transition done, time: 19019 us
```

#### Per-task consistency model:
```shell
[107846.049951] Xkernel consistency module loaded
[107846.049956] Per-task consistency model is enabled
[107846.547789] stop_machine overhead: 49 us
[107846.547832] [Target Functions] [ksys_mmap_pgoff] at 0xffffffffbb2354a0 with span [0x43, 0x6c]
[107846.549399] Function ksys_mmap_pgoff[0x43, 0x6c] found in stack trace for task [test 0/149862]
[107846.549405] Stack trace for task [test 0]:
[107846.549406]   [0] vm_mmap_pgoff+0xc0/0x1a0
[107846.549412]   [1] ksys_mmap_pgoff+0x4a/0x270
[107846.549416]   [2] __x64_sys_mmap+0x33/0x70
[107846.549420]   [3] x64_sys_call+0x1fce/0x25a0
[107846.549424]   [4] do_syscall_64+0x7f/0x180
[107846.549428]   [5] entry_SYSCALL_64_after_hwframe+0x78/0x80
[107846.549432] Function ksys_mmap_pgoff[0x43, 0x6c] found in stack trace for task [test 1/149864]
[107846.549434] Stack trace for task [test 1]:
[107846.549435]   [0] vm_mmap_pgoff+0xc0/0x1a0
[107846.549437]   [1] ksys_mmap_pgoff+0x4a/0x270
[107846.549440]   [2] __x64_sys_mmap+0x33/0x70
[107846.549442]   [3] x64_sys_call+0x1fce/0x25a0
[107846.549444]   [4] do_syscall_64+0x7f/0x180
[107846.549447]   [5] entry_SYSCALL_64_after_hwframe+0x78/0x80
[107846.549450] Function ksys_mmap_pgoff[0x43, 0x6c] found in stack trace for task [test 2/149865]
[107846.549451] Stack trace for task [test 2]:
[107846.549452]   [0] vm_mmap_pgoff+0xc0/0x1a0
[107846.549455]   [1] ksys_mmap_pgoff+0x4a/0x270
[107846.549457]   [2] __x64_sys_mmap+0x33/0x70
[107846.549459]   [3] x64_sys_call+0x1fce/0x25a0
[107846.549461]   [4] do_syscall_64+0x7f/0x180
[107846.549464]   [5] entry_SYSCALL_64_after_hwframe+0x78/0x80
[107846.549467] Function ksys_mmap_pgoff[0x43, 0x6c] found in stack trace for task [test 4/149867]
[107846.549469] Stack trace for task [test 4]:
[107846.549470]   [0] vm_mmap_pgoff+0xc0/0x1a0
[107846.549472]   [1] ksys_mmap_pgoff+0x4a/0x270
[107846.549475]   [2] __x64_sys_mmap+0x33/0x70
[107846.549477]   [3] x64_sys_call+0x1fce/0x25a0
[107846.549479]   [4] do_syscall_64+0x7f/0x180
[107846.549481]   [5] entry_SYSCALL_64_after_hwframe+0x78/0x80
[107846.549521] [Transition] Waiting for transition to be done or failed
[107846.552324] Task has finished its transition, freeing refcount, time cost: 2889us
[107846.552332] Task has finished its transition, freeing refcount, time cost: 2863us
[107846.553322] Task has finished its transition, freeing refcount, time cost: 3917us
[107846.553336] Task has finished its transition, freeing refcount, time cost: 3884us
```

## Case Studies

Cases are summarized in [CaseStudy](xkernel/tools/CaseStudy/constant.md).

## Analyze Git History of Constant Changes

The `analyze_symbol_changes.py` script is a powerful tool for analyzing changes of kernel symbols across different kernel versions. It can track how constants, macros, and other symbols have evolved throughout the Linux kernel development history.

### Features

- **Multi-threaded Analysis**: Parallel processing for faster analysis across large version ranges
- **Flexible Symbol Input**: Support for single symbols, comma-separated lists, or symbols from files

### Basic Usage

```bash
# Analyze a single symbol
python xkernel/tools/misc/analyze_symbol_changes.py SMC_TX_WORK_DELAY --kernel-path ~/linux --start-version v5.0 --end-version v5.2

# Analyze multiple symbols
python xkernel/tools/misc/analyze_symbol_changes.py "SMC_TX_WORK_DELAY,MAX_GRO_SKBS" --kernel-path ~/linux

# Use symbols from a file
python xkernel/tools/misc/analyze_symbol_changes.py --symbols-file symbols.txt --kernel-path ~/linux
```

### Command Line Options
<details>
<summary>Click to expand: Command line options</summary>

```bash
python xkernel/tools/misc/analyze_symbol_changes.py [SYMBOL] [OPTIONS]

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
python3 xkernel/tools/misc/analyze_symbol_changes.py -sf symbol.csv -k ~/linux -q -d
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
18e537cd | Thu Sep 21 [v4.14-rc1] | net/smc: introduce a delay | #define SMC_TX_WORK_DELAY     HZ
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
python3 xkernel/tools/misc/analyze_symbol_changes.py -sf symbol.csv -k ~/linux -d -v
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
python3 xkernel/tools/misc/analyze_symbol_changes.py SMC_TX_WORK_DELAY -k ~/linux -d -vv
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
