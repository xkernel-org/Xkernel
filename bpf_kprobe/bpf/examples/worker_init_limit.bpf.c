// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/create_worker_cont+0xb5")
int BPF_KPROBE(create_worker_cont_0xb5){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0x1){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0xb5\n");
    }
    bpf_printk("0xb5\n");
    return 0;
}

SEC("kprobe/create_io_worker+0x127")
int BPF_KPROBE(create_io_worker_0x127){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0x1){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x127\n");
    }
    bpf_printk("0x127\n");
    return 0;
}