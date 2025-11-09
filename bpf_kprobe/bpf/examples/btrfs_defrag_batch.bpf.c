// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/btrfs_run_defrag_inode.isra.0+0x186")
int BPF_KPROBE(btrfs_run_defrag_inode_isra_0_0x186){
    BPF_SET_R8(ctx, 0x800);
    bpf_printk("0x186\n");
    return 0;
}