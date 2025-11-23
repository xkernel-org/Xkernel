// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/btrfs_async_run_delayed_root+0x1b6")
int BPF_KPROBE(btrfs_async_run_delayed_root_0x1b6){
    u64 rbp = BPF_RBP(ctx);
    u64 *addr = (u64 *)(rbp - 0x44);
    u64 value;
    bpf_probe_read_kernel(&value, sizeof(u64), addr);
    if(value <= 0xff){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x1b6\n");
    }
    bpf_printk("0x1b6\n");
    return 0;
}

SEC("kprobe/btrfs_balance_delayed_items+0x7f")
int BPF_KPROBE(btrfs_balance_delayed_items_0x7f){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0xff){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x7f\n");
    }
    bpf_printk("0x7f\n");
    return 0;

}