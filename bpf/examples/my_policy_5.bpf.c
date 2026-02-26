// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 5

#include "my_policy_5.internal.bpf.h"

// Kprobe 1: __blk_mq_sched_dispatch_requests+0x57c (simple)
// Candidates: 0x57c,0x57f
// Relationship: IV = V
X_TUNE_0(__blk_mq_sched_dispatch_requests, "+0x57c") {
    if (!x_transition_done(x_ctx)) return 0;

    // Get tunable value (V=3 originally)
    u64 val = 3; // TODO: Read from BPF map
    x_set(x_ctx, val);
    return 0;
}

// Kprobe 2: __blk_mq_sched_dispatch_requests+0x5c9 (simple)
// Candidates: 0x5c9,0x5cc
// Relationship: IV = V
X_TUNE_1(__blk_mq_sched_dispatch_requests, "+0x5c9") {
    if (!x_transition_done(x_ctx)) return 0;

    // Get tunable value (V=3 originally)
    u64 val = 3; // TODO: Read from BPF map
    x_set(x_ctx, val);
    return 0;
}
