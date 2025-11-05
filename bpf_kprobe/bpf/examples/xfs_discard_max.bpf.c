// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/xfs_trim_gather_extents+0x12c")
int BPF_KPROBE(xfs_trim_gather_extents_0x12c){
    BPF_SET_EAX(ctx, 0xc8);
    bpf_printk("0x12c\n");
    return 0;
}

SEC("kprobe/xfs_trim_rtgroup_extents+0x135")
int BPF_KPROBE(xfs_trim_rtgroup_extents_0x135){
    u64 rbp = BPF_RBP(ctx);
    u64 *addr = (u64 *)(rbp - 0x38);
    u64 value = 0xc8;
    kfuncs_probe_write_kernel(addr, sizeof(u64), &value, sizeof(u64));
    bpf_printk("0x134\n");
    return 0;
}