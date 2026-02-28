// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 2

#include "my_policy_2.internal.bpf.h"

// Kprobe 1: blk_mq_dispatch_rq_list+0x406 (simple)
// Candidates: 0x406,0x409
// Relationship: IV = V
X_TUNE_0(blk_mq_dispatch_rq_list, "+0x406") {
    if (!x_transition_done(x_ctx)) return 0;

    // Get tunable value (V=3 originally)
    u64 val = 3; // TODO: Read from BPF map
    x_set(x_ctx, val);
    return 0;
}
