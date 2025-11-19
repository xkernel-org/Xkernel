// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/get_any_page+0xa8")
int BPF_KPROBE(get_any_page_0xa8){
    u64 r13 = BPF_R13(ctx);
    if(r13 == 0x2){
        BPF_SET_JE_TRUE(ctx);
        bpf_printk("0xa8\n");
    }
    bpf_printk("0xa8\n");
    return 0;
}

SEC("kprobe/get_any_page+0xf7")
int BPF_KPROBE(get_any_page_0xf7){
    u64 r13 = BPF_R13(ctx);
    if(r13 == 0x2){
        BPF_SET_JE_TRUE(ctx);
        bpf_printk("0xf7\n");
    }
    bpf_printk("0xf7\n");
    return 0;
}


SEC("kprobe/get_any_page+0x23b")
int BPF_KPROBE(get_any_page_0x23b){
    u64 r13 = BPF_R13(ctx);
    if(r13 != 0x2){
        BPF_SET_JNE_TRUE(ctx);
        bpf_printk("0x23b\n");
    }
    bpf_printk("0x23b\n");
    return 0;
}

SEC("kprobe/get_any_page+0x2ab")
int BPF_KPROBE(get_any_page_0x2ab){
    u64 r13 = BPF_R13(ctx);
    if(r13 != 0x2){
        BPF_SET_JNE_TRUE(ctx);
        bpf_printk("0x2ab\n");
    }
    bpf_printk("0x2ab\n");
    return 0;
}

