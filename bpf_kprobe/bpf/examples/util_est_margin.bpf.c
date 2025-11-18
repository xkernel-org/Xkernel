// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/dequeue_task_fair+0x77")
int BPF_KPROBE(dequeue_task_fair_0x77){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0x4){
        BPF_SET_JBE_TRUE(ctx);
        bpf_printk("0x77\n");
    }
    bpf_printk("0x77\n");
    return 0;
}

SEC("kprobe/dequeue_task_fair+0xad")
int BPF_KPROBE(dequeue_task_fair_0xad){
    u64 r15 = BPF_R15(ctx);
    BPF_SET_R15(ctx, r15 - 0x5);
    bpf_printk("0xad\n");
    return 0;
}