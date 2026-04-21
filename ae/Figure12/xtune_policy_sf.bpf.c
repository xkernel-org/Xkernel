// SPDX-License-Identifier: GPL-2.0
// RTT-aware X_TUNE policy for tcp_cubic SF (ConstID 1)
// Only sets SF=1 when the socket's curr_rtt >= 40ms
//
// tune_tcp_cubic.sh patches the function name and offset below to match
// the running kernel (hystart_update standalone vs inlined into cubictcp_acked).

#include "xtune_stub_1.bpf.h"

#define ICSK_CA_PRIV_OFF  1280   /* inet_connection_sock.icsk_ca_priv offset */
#define BICTCP_CURR_RTT_OFF 56   /* bictcp.curr_rtt offset within ca_priv */
#define RTT_THRESHOLD     40000  /* 40ms in usec — between 20ms and 80ms RTT flows */

// Kprobe at hystart_update+0x164 (or cubictcp_acked+0x214 if inlined)
// At this point, RBX holds sk (used for struct accesses throughout the BB)
X_TUNE_0(hystart_update, "+0x164") {
    if (!x_transition_done(x_ctx)) return 0;

    u64 sk = ctx->bx;
    u32 cur_rtt = 0;
    u64 rtt_addr = sk + ICSK_CA_PRIV_OFF + BICTCP_CURR_RTT_OFF;
    bpf_probe_read_kernel(&cur_rtt, sizeof(cur_rtt), (void *)rtt_addr);

    if (cur_rtt >= RTT_THRESHOLD)
        x_set(x_ctx, 1);  // SF=1 for high-RTT flows

    return 0;
}
