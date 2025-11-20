// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/io_iopoll_check+0xa9")
int BPF_KPROBE(io_iopoll_check_0xa9){
    BPF_SET_ECX(ctx, 0xa);
    bpf_printk("0xa9\n");
    return 0;
}

SEC("kprobe/__do_sys_io_uring_enter+0x3fa")
int BPF_KPROBE(__do_sys_io_uring_enter_0x3fa){
    BPF_SET_EAX(ctx, 0xa);
    bpf_printk("0x3fa\n");
    return 0;   
}

/*
SEC("kprobe/__do_sys_io_uring_enter")
int BPF_KPROBE(__do_sys_io_uring_enter_entry){
    bpf_printk("entry\n");
    return 0;   
}
*/


SEC("kprobe/io_run_task_work_sig+0x53")
int BPF_KPROBE(io_run_task_work_sig_0x53){
    BPF_SET_ECX(ctx, 0xa);
    bpf_printk("0x53\n");
    return 0; 
}

SEC("kprobe/io_cqring_wait+0x7a")
int BPF_KPROBE(io_cqring_wait_0x7a){
    BPF_SET_ECX(ctx, 0xa);
    bpf_printk("0x7a\n");
    return 0;  
}