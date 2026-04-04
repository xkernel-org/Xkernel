# Example X-tune Policies

These examples demonstrate the KernelX programmable policy plane (§3.6 of the paper).
Each file is a self-contained X-tune policy that can be loaded with `xkernel-tool`.

## Files

| File | Paper Reference | Description |
|------|----------------|-------------|
| `tcp_cubic_hystart.bpf.c` | Fig. 7 | RTT-aware HyStart scaling factor for TCP CUBIC |
| `rocksdb_hint.bpf.c` | Fig. 23 | Application-informed per-thread tuning for RocksDB |
| `zswap_shrinker.bpf.c` | Fig. 24 | Per-shrinker SHRINK_BATCH for zswap only |
| `merge_failure_adaptive.bpf.c` | Fig. 25 | Adaptive BLK_MAX_REQUEST_COUNT via merge tracking |

## How to Use

1. Build the corresponding tunable:
   ```bash
   ./xkernel-tool build tunables/shrink_batch.toml
   ```

2. Copy an example and adapt the `#include` to match your ConstID's stub header:
   ```bash
   cp examples/policy/zswap_shrinker.bpf.c bpf/stubs/xtune_stub_1.bpf.c
   # Edit the #include line to match: #include "xtune_stub_1.bpf.h"
   ```

3. Recompile and load:
   ```bash
   make -C bpf/
   sudo ./xkernel-tool load 0 1
   ```

## Writing Your Own Policy

An X-tune policy follows this pattern:

```c
#include "xtune_stub_N.bpf.h"   // auto-generated SIE internals

X_TUNE_0(kernel_function, "+0xOFFSET") {
    // 1. Safety guard (mandatory — must be first)
    if (!x_transition_done(x_ctx)) return 0;

    // 2. Read kernel state via ctx (pt_regs)
    struct sock *sk = (struct sock *)PT_REGS_PARM1(ctx);

    // 3. Policy logic
    u64 new_value = compute_optimal_value(sk);

    // 4. Apply
    x_set(x_ctx, new_value);
    return 0;
}
```

Key APIs:
- `x_transition_done(x_ctx)` — Check if it's safe to apply new values
- `x_set(x_ctx, val)` — Set the perf-const to a new source-level value
- `PT_REGS_PARM1(ctx)` through `PT_REGS_PARM5(ctx)` — Read function parameters
- `BPF_CORE_READ(ptr, field)` — Safely read kernel struct fields
- Standard BPF helpers: `bpf_get_current_pid_tgid()`, `bpf_get_smp_processor_id()`, etc.
