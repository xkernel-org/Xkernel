// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/get_next_ino+0x1f")
int BPF_KPROBE(get_next_ino_0x1f){
    u64 eax = BPF_EAX(ctx);
    if((eax & 0x1ff) == 0){
        BPF_SET_ZF_TRUE(ctx);
        bpf_printk("0x1f\n");
    }
    return 0;
}

SEC("kprobe/get_next_ino+0x49")
int BPF_KPROBE(get_next_ino_0x49){
    BPF_SET_EAX(ctx, 0x200);
    bpf_printk("0x49\n");
    return 0;
}