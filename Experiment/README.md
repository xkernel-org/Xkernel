The `Experiment` directory covers all PerfConsts (performance-related macros) in the `fs`, `mm`, `kernel/sched`, and `io_uring` subsystems that appear in the following list:
[https://docs.google.com/document/d/1bjzkT3hZSjEuCb7AUvWvECTc9gCNchNw1MGpAqa-gSk/edit?tab=t.0](https://docs.google.com/document/d/1bjzkT3hZSjEuCb7AUvWvECTc9gCNchNw1MGpAqa-gSk/edit?tab=t.0)

In total, we examined **76** PerfConsts from these subsystems.

* **14** PerfConsts are labeled **HARD TO TRIGGER**.
  This can happen for several reasons, for example:

  * They require heterogeneous memory devices to form fast and slow tiers (e.g., `NUMA_MIGRATION_ADJUST_STEPS`).
  * Their code paths are only executed once during early boot initialization (e.g., `RCU_JIFFIES_FQS_DIV`).
  * Or, more simply, we were unable to find a reasonably simple way to exercise the corresponding kernel paths (e.g., `MMAP_LOTSAMISS`, `PCPU_SLOT_FAIL_THRESHOLD`).

* **5** PerfConsts are labeled **NOT IN CONSIDERATION**.
  Again, this category covers different situations. A typical example is a macro whose semantics define a maximum “grace time” after a user has exceeded their quota, during which tmpfs still allows writes (e.g., `SHMEM_MAX_DQ_TIME`). Such PerfConsts are mainly about defining policy limits rather than performance-critical behavior.

* The remaining **57** PerfConsts were successfully triggered. Stress testing confirmed that enabling their instrumentation and running the corresponding workloads does not cause any harmful behavior to the system.

The `Experiment` tree is organized by subsystem and **only contains those PerfConsts for which we have a successful trigger method** (i.e., the 57 PerfConsts above). For each PerfConst in the tree, its trigger method falls into exactly one of the following categories:

1. **Automatically triggered**
   The kprobe loader (`kprobe_loader`) only needs to attach; the relevant code path will be exercised automatically during normal system operation. This is usually documented at the end of the corresponding `objdump.txt` for that PerfConst, e.g., `MAX_SCAN_WINDOW`.

2. **Triggered by a script or standalone program**
   The PerfConst is exercised by running a provided script (e.g., `run.sh`) or a userspace program (e.g., `./t`, compiled from the `t.c` in that PerfConst’s directory). For example, `MAX_PINNED_INTERVAL`.

3. **Triggered by sharing a workload with another PerfConst**
   Some PerfConsts are triggered by reusing workloads designed for another PerfConst. For example, `DEF_PRIORITY` and `MAX_INOBT_WALK_PREFETCH` share workloads with other PerfConsts.

4. **Requires relatively complex setup and preparation**
   Due to their inherent complexity or the requirements of the runtime environment, these PerfConsts require more elaborate configuration and preparation to trigger. For example, `SHRINK_BATCH` and `XFS_ICOUNT_BATCH`.

For more details on each PerfConst, please refer to the comments at the end of the corresponding `objdump.txt` or its `README.md` file.