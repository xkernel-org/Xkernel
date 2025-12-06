#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/io_issue_sqe")
int BPF_KPROBE(io_issue_sqe) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_poll_issue")
int BPF_KPROBE(io_poll_issue) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_wq_submit_work")
int BPF_KPROBE(io_wq_submit_work) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_uring_cmd_prep")
int BPF_KPROBE(io_uring_cmd_prep) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_uring_cmd")
int BPF_KPROBE(io_uring_cmd) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_uring_cmd_mark_cancelable")
int BPF_KPROBE(io_uring_cmd_mark_cancelable) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_uring_try_cancel_uring_cmd")
int BPF_KPROBE(io_uring_try_cancel_uring_cmd) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_req_uring_cleanup")
int BPF_KPROBE(io_req_uring_cleanup) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_poll_task_func")
int BPF_KPROBE(io_poll_task_func) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_poll_wake")
int BPF_KPROBE(io_poll_wake) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/__io_queue_proc")
int BPF_KPROBE(__io_queue_proc) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_poll_queue_proc")
int BPF_KPROBE(io_poll_queue_proc) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_poll_add_hash")
int BPF_KPROBE(io_poll_add_hash) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/__io_arm_poll_handler")
int BPF_KPROBE(__io_arm_poll_handler) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_async_queue_proc")
int BPF_KPROBE(io_async_queue_proc) {
    per_task_transition_handler(ctx);
    return 0;
}

#endif
