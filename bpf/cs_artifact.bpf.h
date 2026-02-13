#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/io_cqring_wait+0x75")
int BPF_KPROBE(io_cqring_wait_75) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/__do_sys_io_uring_enter+0x326")
int BPF_KPROBE(__do_sys_io_uring_enter_326) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/__do_sys_io_uring_enter+0x524")
int BPF_KPROBE(__do_sys_io_uring_enter_524) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/io_run_task_work_sig+0x61")
int BPF_KPROBE(io_run_task_work_sig_61) {
    per_task_transition_handler(ctx);
    return 0;
}

#endif
