// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 4

#include "xtune_stub_4.bpf.h"

// void tcp_rack_detect_loss(struct sock * sk, u32 * reo_timeout)
// Kprobe 1: tcp_rack_detect_loss+0x6e (irreversible)
// Candidates: 0x6e
// Relationship: IV = V
X_TUNE_0(tcp_rack_detect_loss, "+0x6e") {
    if (!x_transition_done(x_ctx)) return 0;

    // Get tunable value (V=2 originally)
    u64 val = 2;
    x_set(x_ctx, val);
    // Write your tuning logic here
    return 0;
}
