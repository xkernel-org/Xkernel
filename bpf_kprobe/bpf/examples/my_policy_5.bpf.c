// SPDX-License-Identifier: GPL-2.0
// Auto-generated for test group 5

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "util.bpf.h"

// Kprobe 1: __blk_mq_sched_dispatch_requests+0x58a
// Relationship: IV = V
SEC("kprobe/__blk_mq_sched_dispatch_requests+0x58a")
int BPF_KPROBE(__blk_mq_sched_dispatch_requests_0x58a) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=3 originally)
    u64 val = 3; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_ESI(ctx, val);

    return 0;
}

// Kprobe 2: __blk_mq_sched_dispatch_requests+0x5a8
// Relationship: IV = V
SEC("kprobe/__blk_mq_sched_dispatch_requests+0x5a8")
int BPF_KPROBE(__blk_mq_sched_dispatch_requests_0x5a8) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=3 originally)
    u64 val = 3; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_ESI(ctx, val);

    return 0;
}
