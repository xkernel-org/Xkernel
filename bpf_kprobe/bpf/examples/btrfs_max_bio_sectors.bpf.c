// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/btrfs_dio_iomap_begin+0x96")
int BPF_KPROBE(btrfs_dio_iomap_begin_0x96){
    u64 eax = BPF_EAX(ctx);
    eax = eax >> 1;
    BPF_SET_EAX(ctx, eax);
    bpf_printk("0x96\n");
    return 0;
}