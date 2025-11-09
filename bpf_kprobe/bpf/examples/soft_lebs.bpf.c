// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/ubifs_garbage_collect+0xcf")
int BPF_KPROBE(ubifs_garbage_collect_0xcf){
    u64 r12 = BPF_R12(ctx);
    if(r12 <= 0x4){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0xcf\n");
    }
    return 0;
}


SEC("kprobe/ubifs_garbage_collect+0x111")
int BPF_KPROBE(ubifs_garbage_collect_0x111){
    u64 r12 = BPF_R12(ctx);
    if(r12 <= 0x5){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x111\n");
    }
    return 0;
}


SEC("kprobe/ubifs_garbage_collect+0x25f")
int BPF_KPROBE(ubifs_garbage_collect_0x25f){
    u64 r12 = BPF_R12(ctx);
    if(r12 > 0x4){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x25f\n");
    }
    return 0;
}

