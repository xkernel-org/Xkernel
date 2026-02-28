// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 5

#include "xtune_stub_5.bpf.h"

// void tcp_rack_detect_loss(struct sock * sk, u32 * reo_timeout)
// Kprobe 1: tcp_rack_detect_loss+0x6e (irreversible)
// Candidates: 0x6e
// Relationship: IV = V
X_TUNE_0(tcp_rack_detect_loss, "+0x6e") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 2; // original value
    x_set(x_ctx, val);
    return 0;
}
