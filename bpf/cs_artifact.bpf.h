#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include "xkernel.bpf.h"

// Guard: io_run_task_work_sig+0x4b (SS entry)
SEC("kprobe/io_run_task_work_sig+0x4b")
int BPF_KPROBE(__xk_guard_io_run_task_work_sig_4b) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: io_run_task_work_sig+0x6b (SS exit)
SEC("kprobe/io_run_task_work_sig+0x6b")
int BPF_KPROBE(__xk_unguard_io_run_task_work_sig_6b) {
    ss_unguard_handler(ctx);
    return 0;
}

// Guard: io_uring_try_cancel_requests+0x97b (SS entry)
SEC("kprobe/io_uring_try_cancel_requests+0x97b")
int BPF_KPROBE(__xk_guard_io_uring_try_cancel_requests_97b) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: io_uring_try_cancel_requests+0x152 (SS exit)
SEC("kprobe/io_uring_try_cancel_requests+0x152")
int BPF_KPROBE(__xk_unguard_io_uring_try_cancel_requests_152) {
    ss_unguard_handler(ctx);
    return 0;
}

// Guard: __do_sys_io_uring_enter+0x24c (SS entry)
SEC("kprobe/__do_sys_io_uring_enter+0x24c")
int BPF_KPROBE(__xk_guard___do_sys_io_uring_enter_24c) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: __do_sys_io_uring_enter+0x2b9 (SS exit)
SEC("kprobe/__do_sys_io_uring_enter+0x2b9")
int BPF_KPROBE(__xk_unguard___do_sys_io_uring_enter_2b9) {
    ss_unguard_handler(ctx);
    return 0;
}

#endif
