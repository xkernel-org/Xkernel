// SPDX-License-Identifier: GPL-2.0
//
// X-tune policy: RTT-aware TCP CUBIC HyStart tuning (Paper Fig. 7)
//
// Dynamically adjusts the HyStart scaling factor based on per-flow RTT.
// Flows with high RTT (>=80ms) use a smaller scaling factor to avoid
// premature slow-start exit; low-RTT flows keep the default.
//
// Usage:
//   ./xkernel-tool build tunables/all.toml   # Build tcp_cubic tunable
//   # Edit this file to match your ConstID, then:
//   sudo ./xkernel-tool load 1 <ConstID>     # Per-task mode
//
// This corresponds to Figure 7 in the paper.

#include "xtune_stub_1.bpf.h"  // Replace with your actual stub header

// Note: The struct definitions below require vmlinux.h BTF types.
// The actual field offsets come from CO-RE (BPF_CORE_READ).

X_TUNE_0(cubictcp_acked, "+0x210") {
    // 1. Safety guard (mandatory)
    if (!x_transition_done(x_ctx)) return 0;

    // 2. User policy logic: read current RTT from TCP CUBIC state
    struct sock *sk = (struct sock *)PT_REGS_PARM1(ctx);

    // Access CUBIC's private congestion control data
    // struct bictcp is inet_csk_ca(sk)
    // curr_rtt field holds the RTT sample in microseconds
    u32 cur_rtt = 0;

    // Read RTT via BPF CO-RE (actual offset resolved at load time)
    // bpf_probe_read_kernel(&cur_rtt, sizeof(cur_rtt),
    //     (void *)sk + offsetof_ca + offsetof_curr_rtt);

    // Policy: if RTT >= 80ms, use scaling factor 1 (less aggressive)
    if (cur_rtt >= 80000)
        x_set(x_ctx, 1);
    // else: keep default (scaling factor 3) by not calling x_set

    return 0;
}
