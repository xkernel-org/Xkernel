// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/finish_one_item+0x27")
int BPF_KPROBE(finish_one_item_0x27){
    // need new design, pre and post handler
    return 0;
}


SEC("kprobe/btrfs_balance_delayed_items+0xae")
int BPF_KPROBE(btrfs_balance_delayed_items_0xae){
    u64 r13 = BPF_R13(ctx);
    BPF_SET_EBX(ctx, r13 + 0x20);
    bpf_printk("0xae\n");
    return 0;
}


SEC("kprobe/btrfs_balance_delayed_items+0x138")
int BPF_KPROBE(btrfs_balance_delayed_items_0x138){
    BPF_SET_EDX(ctx, 0x20);
    bpf_printk("0x138\n");
    return 0;
}