// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/madvise_vma_behavior+0x4b7")
int BPF_KPROBE(madvise_vma_behavior_0x4b7){
    BPF_SET_R12(ctx, 0x2);
    bpf_printk("0x4b7\n");
    return 0;
}