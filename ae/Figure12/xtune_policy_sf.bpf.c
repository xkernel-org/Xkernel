// SPDX-License-Identifier: GPL-2.0
// RTT-aware X_TUNE policy for tcp_cubic SF (ConstID 1)
// Only sets SF=1 when the socket's curr_rtt >= 80ms
//
// hystart_update is inlined into cubictcp_acked in the running kernel.
// The kprobe offset is the vmlinux offset within cubictcp_acked.

#include "xtune_stub_1.bpf.h"

#define ICSK_CA_PRIV_OFF  1280   /* inet_connection_sock.icsk_ca_priv offset */
#define BICTCP_CURR_RTT_OFF 56   /* bictcp.curr_rtt offset within ca_priv */
#define RTT_THRESHOLD     80000  /* 80ms in usec */

// Kprobe at cubictcp_acked+0x214 (inlined hystart_update)
// At this point, RBX holds sk (used for struct accesses throughout the BB)
X_TUNE_0(cubictcp_acked, "+0x214") {
    if (!x_transition_done(x_ctx)) return 0;

    u64 sk = ctx->bx;
    u32 cur_rtt = 0;
    u64 rtt_addr = sk + ICSK_CA_PRIV_OFF + BICTCP_CURR_RTT_OFF;
    bpf_probe_read_kernel(&cur_rtt, sizeof(cur_rtt), (void *)rtt_addr);

    if (cur_rtt >= RTT_THRESHOLD)
        x_set(x_ctx, 1);  // SF=1 for high-RTT flows

    return 0;
}
