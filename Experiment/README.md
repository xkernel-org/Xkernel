The `Experiment` directory covers all macros in the `fs`, `mm`, `kernel/sched`, and `io_uring` subsystems that appear in the following list:
[https://docs.google.com/document/d/1bjzkT3hZSjEuCb7AUvWvECTc9gCNchNw1MGpAqa-gSk/edit?tab=t.0](https://docs.google.com/document/d/1bjzkT3hZSjEuCb7AUvWvECTc9gCNchNw1MGpAqa-gSk/edit?tab=t.0)

In total, 74 macros from these subsystems were tested.

* **13** macros are labeled **HARD TO TRIGGER**.
  This may be for several reasons, for example:

  * They require heterogeneous memory devices to form fast and slow tiers (e.g., `NUMA_MIGRATION_ADJUST_STEPS`).
  * Their code paths are only executed once during early boot / initialization (e.g., `RCU_JIFFIES_FQS_DIV`).
  * Or, more simply, we were unable to find a reasonably simple way to exercise the corresponding kernel paths (e.g., `MMAP_LOTSAMISS`, `PCPU_SLOT_FAIL_THRESHOLD`).

* **5** macros are labeled **NOT IN CONSIDERATION**.
  Again, this category covers different situations. A typical example is a macro whose semantics define a maximum “grace time” after a user has exceeded their quota, during which tmpfs still allows writes (e.g., `SHMEM_MAX_DQ_TIME`). Such macros are more about defining policy limits than about performance-critical behavior.

* **56** macros were successfully triggered, and stress testing confirmed that enabling their instrumentation and workloads does not cause any harmful behavior to the system.

The `Experiment` tree is organized by subsystem and only contains PerfConsts (performance-related constants/macros) for which we have a successful trigger test. For any given PerfConst, its trigger method falls into exactly one of the following categories:

1. **Automatically triggered**
   The kprobe loader (`kprobe_loader`) only needs to attach; the relevant code path will be exercised automatically during normal system operation. This is usually documented at the end of the corresponding `objdump.txt` for that PerfConst.

2. **Triggered by a script or standalone program**
   The PerfConst is exercised by running a provided script (e.g., `run.sh`) or a userspace program (e.g., `./t`, compiled from the `t.c` in that PerfConst’s directory).

3. **Triggered by sharing a workload with another PerfConst**
   Some PerfConsts share the same directory and are triggered by reusing the workload designed for another PerfConst in that path.

For any PerfConst you want to test, please carefully read all files in its directory to understand how it is triggered and how the workload is intended to be used.
