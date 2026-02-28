// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 1

#include "my_policy_1.internal.bpf.h"

// Kprobe 1: cubictcp_acked+0x21a (irreversible)
// Candidates: 0x21a
// Relationship: IV = V
X_TUNE_0(cubictcp_acked, "+0x21a") {
    if (!x_transition_done(x_ctx)) return 0;

    // Get tunable value (V=3 originally)
    u64 val = 3; // TODO: Read from BPF map
    x_set(x_ctx, val);
    return 0;
}
