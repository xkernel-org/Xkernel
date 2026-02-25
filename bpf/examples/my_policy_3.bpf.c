// SPDX-License-Identifier: GPL-2.0
// Auto-generated for test group 3

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "util.bpf.h"

// Kprobe 1: io_cqring_wait+0x7c
// Candidates: 0x7c,0x7f,0x82
// Relationship: IV = V
SEC("kprobe/io_cqring_wait+0x7c")
int BPF_KPROBE(io_cqring_wait_0x7c) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=20 originally)
    u64 val = 20; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_ECX(ctx, val);

    return 0;
}

// Kprobe 2: __do_sys_io_uring_enter+0x264
// Candidates: 0x264,0x268,0x26a,0x271,0x272,0x275
// Relationship: IV = V
SEC("kprobe/__do_sys_io_uring_enter+0x264")
int BPF_KPROBE(__do_sys_io_uring_enter_0x264) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=20 originally)
    u64 val = 20; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_EAX(ctx, val);

    return 0;
}

// Kprobe 3: __do_sys_io_uring_enter+0x6bb
// Candidates: 0x6bb,0x6bf,0x6c2
// Relationship: IV = V
SEC("kprobe/__do_sys_io_uring_enter+0x6bb")
int BPF_KPROBE(__do_sys_io_uring_enter_0x6bb) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=20 originally)
    u64 val = 20; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_EAX(ctx, val);

    return 0;
}

// Kprobe 4: io_run_task_work_sig+0x53
// Candidates: 0x53,0x58,0x5c
// Relationship: IV = V
SEC("kprobe/io_run_task_work_sig+0x53")
int BPF_KPROBE(io_run_task_work_sig_0x53) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=20 originally)
    u64 val = 20; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_ECX(ctx, val);

    return 0;
}
