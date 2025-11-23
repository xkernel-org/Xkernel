// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// finish_one_item
SEC("kprobe/finish_one_item+0x1f")
int BPF_KPROBE(finish_one_item_0x1f){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0x3f){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x1f\n");
    }
    bpf_printk("0x1f\n");
    return 0;
}

// btrfs_async_run_delayed_root
SEC("kprobe/btrfs_async_run_delayed_root+0x50")
int BPF_KPROBE(btrfs_async_run_delayed_root_0x50){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0x1f){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x50\n");
    }
    bpf_printk("0x50\n");
    return 0;
}

SEC("kprobe/btrfs_async_run_delayed_root+0x213")
int BPF_KPROBE(btrfs_async_run_delayed_root_0x213){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0x1f){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x213\n");
    }
    bpf_printk("0x213\n");
    return 0;
}


// btrfs_balance_delayed_items
SEC("kprobe/btrfs_balance_delayed_items+0x32")
int BPF_KPROBE(btrfs_balance_delayed_items_0x32){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0x3f){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x32\n");
    }
    bpf_printk("0x32\n");
    return 0; 
}

SEC("kprobe/btrfs_balance_delayed_items+0xba")
int BPF_KPROBE(btrfs_balance_delayed_items_0xba){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0x3f){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x32\n");
    }
    bpf_printk("0x32\n");
    return 0; 
}

SEC("kprobe/btrfs_balance_delayed_items+0x121")
int BPF_KPROBE(btrfs_balance_delayed_items_0x121){
    u64 edx = BPF_EDX(ctx);
    if(edx <= 0x3f){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x121\n");
    }
    bpf_printk("0x121\n");
    return 0; 
}