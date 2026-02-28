// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 15

#include "xtune_stub_15.bpf.h"

// int __blk_mq_sched_dispatch_requests(struct blk_mq_hw_ctx * hctx)
// Kprobe 1: __blk_mq_sched_dispatch_requests+0x57c (simple)
// Candidates: 0x57c,0x57f
// Relationship: IV = V
X_TUNE_0(__blk_mq_sched_dispatch_requests, "+0x57c") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 3; // original value
    x_set(x_ctx, val);
    return 0;
}

// int __blk_mq_sched_dispatch_requests(struct blk_mq_hw_ctx * hctx)
// Kprobe 2: __blk_mq_sched_dispatch_requests+0x5c9 (simple)
// Candidates: 0x5c9,0x5cc
// Relationship: IV = V
X_TUNE_1(__blk_mq_sched_dispatch_requests, "+0x5c9") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 3; // original value
    x_set(x_ctx, val);
    return 0;
}
