// SPDX-License-Identifier: GPL-2.0
// Auto-generated for test group 2

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "util.bpf.h"

// Kprobe 1: blk_mq_dispatch_rq_list+0x390
// Relationship: IV = V
SEC("kprobe/blk_mq_dispatch_rq_list+0x390")
int BPF_KPROBE(blk_mq_dispatch_rq_list_0x390) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=3 originally)
    u64 val = 3; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_ESI(ctx, val);

    return 0;
}
