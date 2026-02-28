// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 9

#include "my_policy_9.internal.bpf.h"

// Kprobe 1: blk_add_rq_to_plug+0xd1 (irreversible)
// Candidates: 0xd1
// Relationship: IV = -V + 4294967296
X_TUNE_0(blk_add_rq_to_plug, "+0xd1") {
    if (!x_transition_done(x_ctx)) return 0;

    // Get tunable value (V=32 originally)
    u64 val = 32; // TODO: Read from BPF map
    x_set(x_ctx, val);
    return 0;
}
