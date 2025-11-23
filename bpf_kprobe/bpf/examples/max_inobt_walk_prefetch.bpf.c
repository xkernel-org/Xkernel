// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/xfs_inobt_walk+0x4c")
int BPF_KPROBE(xfs_inobt_walk_0x4c){
    BPF_SET_EAX(ctx, 0x8000);
    bpf_printk("0x4c\n");
    return 0;
}

SEC("kprobe/xfs_inobt_walk+0x6b")
int BPF_KPROBE(xfs_inobt_walk_0x6b){
    BPF_SET_ECX(ctx, 0x8000);
    bpf_printk("0x6b\n");
    return 0;
}


