// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 3

#include "xtune_stub_3.bpf.h"

// int io_cqring_wait(struct io_ring_ctx * ctx, int min_events, u32 flags, struct ext_arg * ext_arg)
// Kprobe 1: io_cqring_wait+0x7c (simple)
// Candidates: 0x7c,0x7f,0x82
// Relationship: IV = V
X_TUNE_0(io_cqring_wait, "+0x7c") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 20; // original value
    x_set(x_ctx, val);
    return 0;
}

// long int __do_sys_io_uring_enter(unsigned int fd, u32 to_submit, u32 min_complete, u32 flags, ? * argp, size_t argsz)
// Kprobe 2: __do_sys_io_uring_enter+0x264 (simple)
// Candidates: 0x264,0x268,0x26a,0x272,0x275
// Relationship: IV = V
X_TUNE_1(__do_sys_io_uring_enter, "+0x264") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 20; // original value
    x_set(x_ctx, val);
    return 0;
}

// long int __do_sys_io_uring_enter(unsigned int fd, u32 to_submit, u32 min_complete, u32 flags, ? * argp, size_t argsz)
// Kprobe 3: __do_sys_io_uring_enter+0x6bb (simple)
// Candidates: 0x6bb,0x6bf,0x6c2
// Relationship: IV = V
X_TUNE_2(__do_sys_io_uring_enter, "+0x6bb") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 20; // original value
    x_set(x_ctx, val);
    return 0;
}

// int io_run_task_work_sig(struct io_ring_ctx * ctx)
// Kprobe 4: io_run_task_work_sig+0x53 (simple)
// Candidates: 0x53,0x58,0x5c
// Relationship: IV = V
X_TUNE_3(io_run_task_work_sig, "+0x53") {
    if (!x_transition_done(x_ctx)) return 0;

    // Write your tuning logic here
    u64 val = 20; // original value
    x_set(x_ctx, val);
    return 0;
}
