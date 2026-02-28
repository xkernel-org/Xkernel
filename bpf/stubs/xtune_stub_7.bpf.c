// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 7

#include "xtune_stub_7.bpf.h"

// long unsigned int do_shrink_slab(struct shrink_control * shrinkctl, struct shrinker * shrinker, int priority)
// Kprobe 1: do_shrink_slab+0xb (simple)
// Candidates: 0xb,0xe,0x10,0x12,0x15,0x17,0x19,0x1a,0x1d,0x21,0x25,0x28,0x2b
// Relationship: IV = V
X_TUNE_0(do_shrink_slab, "+0xb") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 128; // original value
    x_set(x_ctx, val);
    return 0;
}
