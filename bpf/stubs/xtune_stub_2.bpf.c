// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 2

#include "xtune_stub_2.bpf.h"

// void blk_add_rq_to_plug(struct blk_plug * plug, struct request * rq)
// Kprobe 1: blk_add_rq_to_plug+0xcb (irreversible)
// Candidates: 0xcb
// Relationship: IV = -V + 4294967296
X_TUNE_0(blk_add_rq_to_plug, "+0xcb") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 128; // original value
    x_set(x_ctx, val);
    return 0;
}
