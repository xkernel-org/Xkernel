// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 2

#include "xtune_stub_2.bpf.h"

// bool blk_mq_dispatch_rq_list(struct blk_mq_hw_ctx * hctx, struct list_head * list, unsigned int nr_budgets)
// Kprobe 1: blk_mq_dispatch_rq_list+0x406 (simple)
// Candidates: 0x406,0x409
// Relationship: IV = V
X_TUNE_0(blk_mq_dispatch_rq_list, "+0x406") {
    if (!x_transition_done(x_ctx)) return 0;

    // Get tunable value (V=3 originally)
    u64 val = 3;
    x_set(x_ctx, val);
    // Write your tuning logic here
    return 0;
}
