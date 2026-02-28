// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 7

#include "xtune_stub_7.bpf.h"

// void blk_mq_delay_run_hw_queue(struct blk_mq_hw_ctx * hctx, long unsigned int msecs)
// Kprobe 1: blk_mq_delay_run_hw_queue+0xc9 (memory_store)
// Candidates: 0xc9
// Relationship: IV = V
X_TUNE_0(blk_mq_delay_run_hw_queue, "+0xc9") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 8; // original value
    x_set(x_ctx, val);
    return 0;
}

// void blk_mq_map_swqueue(struct request_queue * q)
// Kprobe 2: blk_mq_map_swqueue+0x41e (memory_store)
// Candidates: 0x41e
// Relationship: IV = V
X_TUNE_1(blk_mq_map_swqueue, "+0x41e") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 8; // original value
    x_set(x_ctx, val);
    return 0;
}
