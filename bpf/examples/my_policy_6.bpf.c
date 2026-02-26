// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 6

#include "my_policy_6.internal.bpf.h"

// Kprobe 1: blk_mq_delay_run_hw_queue+0xc9 (memory_store)
// Candidates: 0xc9
// Relationship: IV = V
X_TUNE_0(blk_mq_delay_run_hw_queue, "+0xc9") {
    if (!x_transition_done(x_ctx)) return 0;

    // Get tunable value (V=8 originally)
    u64 val = 8; // TODO: Read from BPF map
    x_set(x_ctx, val);
    return 0;
}

// Kprobe 2: blk_mq_map_swqueue+0x41e (memory_store)
// Candidates: 0x41e
// Relationship: IV = V
X_TUNE_1(blk_mq_map_swqueue, "+0x41e") {
    if (!x_transition_done(x_ctx)) return 0;

    // Get tunable value (V=8 originally)
    u64 val = 8; // TODO: Read from BPF map
    x_set(x_ctx, val);
    return 0;
}
