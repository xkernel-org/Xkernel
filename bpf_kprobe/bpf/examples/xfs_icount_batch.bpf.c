// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/xfs_trans_unreserve_and_mod_sb+0x193")
int BPF_KPROBE(xfs_trans_unreserve_and_mod_sb_0x193){
    BPF_SET_EDX(ctx, 0x40);
    bpf_printk("0x193\n");
    return 0;
}


