// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/xfs_iwalk+0x4c")
int BPF_KPROBE(xfs_iwalk_0x4c){
    BPF_SET_EAX(ctx, 0x14);
    bpf_printk("0x4c\n");
    return 0;
}

SEC("kprobe/xfs_iwalk+0x66")
int BPF_KPROBE(xfs_iwalk_0x66){
    BPF_SET_EAX(ctx, 0x400); 
    bpf_printk("0x66\n");
    return 0;
}


SEC("kprobe/xfs_iwalk_threaded+0x184")
int BPF_KPROBE(xfs_iwalk_threaded_0x184){
    BPF_SET_EAX(ctx, 0x14);
    bpf_printk("0x184\n");
    return 0;
}

SEC("kprobe/xfs_iwalk_threaded+0x1ca")
int BPF_KPROBE(xfs_iwalk_threaded_0x1ca){
    BPF_SET_EAX(ctx, 0x400);
    bpf_printk("0x1ca\n");
    return 0;
}
