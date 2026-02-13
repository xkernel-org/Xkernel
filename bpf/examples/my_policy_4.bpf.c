// SPDX-License-Identifier: GPL-2.0
// Auto-generated for test group 4

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "util.bpf.h"

// Kprobe 1: tcp_rack_detect_loss+0x6e
// Candidates: 0x6e
// Relationship: IV = V
SEC("kprobe/tcp_rack_detect_loss+0x6e")
int BPF_KPROBE(tcp_rack_detect_loss_0x6e) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=2 originally)
    u64 val = 2; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_R15(ctx, val);

    return 0;
}
