// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 3

#include "xtune_stub_3.bpf.h"

// bool blk_mq_dispatch_rq_list(struct blk_mq_hw_ctx * hctx, struct list_head * list, unsigned int nr_budgets)
// Kprobe 1: blk_mq_dispatch_rq_list+0x406 (simple)
// Candidates: 0x406,0x409
// Relationship: IV = V
X_TUNE_0(blk_mq_dispatch_rq_list, "+0x406") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 3; // original value
    x_set(x_ctx, val);
    return 0;
}
