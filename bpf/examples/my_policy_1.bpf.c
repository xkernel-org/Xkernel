// SPDX-License-Identifier: GPL-2.0
// Auto-generated for test group 1

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "util.bpf.h"

// Kprobe 1: cubictcp_acked+0x1f5
// Candidates: 0x1f5
// Relationship: IV = V
SEC("kprobe/cubictcp_acked+0x1f5")
int BPF_KPROBE(cubictcp_acked_0x1f5) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=3 originally)
    u64 val = 3; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_EAX(ctx, val);

    return 0;
}
