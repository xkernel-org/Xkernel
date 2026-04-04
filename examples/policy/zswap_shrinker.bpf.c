// SPDX-License-Identifier: GPL-2.0
//
// X-tune policy: Per-shrinker SHRINK_BATCH tuning (Paper Fig. 24)
//
// The default SHRINK_BATCH (128) applies uniformly to all 43+ kernel shrinkers.
// This X-tune customizes the batch size specifically for the zswap shrinker,
// while leaving other shrinkers at the default.
//
// Usage:
//   ./xkernel-tool build tunables/shrink_batch.toml
//   # Load with: sudo ./xkernel-tool load 0 <ConstID>
//
// This corresponds to Figure 24 in the paper.

#include "xtune_stub_7.bpf.h"  // Replace with actual SHRINK_BATCH stub

X_TUNE_0(do_shrink_slab, "+0x1a3") {
    // 1. Safety guard (mandatory)
    if (!x_transition_done(x_ctx)) return 0;

    // 2. Read the shrinker name from the second parameter
    struct shrinker *s = (struct shrinker *)PT_REGS_PARM2(ctx);
    char name[32];
    if (bpf_probe_read_kernel(name, sizeof(name), &s->name) < 0)
        return 0;

    // 3. Only tune for zswap-shrink; leave others at default
    if (bpf_strncmp(name, 12, "zswap-shrink") == 0) {
        x_set(x_ctx, 64);  // Smaller batch for zswap
    }

    return 0;
}
