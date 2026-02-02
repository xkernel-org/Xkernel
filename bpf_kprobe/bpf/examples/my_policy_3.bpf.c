// SPDX-License-Identifier: GPL-2.0
// Auto-generated for test group 3

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "util.bpf.h"

// Kprobe 1: io_cqring_wait+0x6a
// Relationship: IV = V
SEC("kprobe/io_cqring_wait+0x6a")
int BPF_KPROBE(io_cqring_wait_0x6a) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=20 originally)
    u64 val = 20; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_ECX(ctx, val);

    return 0;
}

// Kprobe 2: __do_sys_io_uring_enter+0x334
// Relationship: IV = V
SEC("kprobe/__do_sys_io_uring_enter+0x334")
int BPF_KPROBE(__do_sys_io_uring_enter_0x334) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=20 originally)
    u64 val = 20; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_EAX(ctx, val);

    return 0;
}

// Kprobe 3: __do_sys_io_uring_enter+0x51c
// Relationship: IV = V
SEC("kprobe/__do_sys_io_uring_enter+0x51c")
int BPF_KPROBE(__do_sys_io_uring_enter_0x51c) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=20 originally)
    u64 val = 20; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_EAX(ctx, val);

    return 0;
}

// Kprobe 4: io_run_task_work_sig+0x59
// Relationship: IV = V
SEC("kprobe/io_run_task_work_sig+0x59")
int BPF_KPROBE(io_run_task_work_sig_0x59) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Get tunable value (V=20 originally)
    u64 val = 20; // TODO: Read from BPF map

    // Apply: IV = V
    BPF_SET_ECX(ctx, val);

    return 0;
}
