// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/alloc_pipe_info+0x196")
int BPF_KPROBE(alloc_pipe_info_0x196){
    BPF_SET_EAX(ctx, 0x3);
    bpf_printk("0x196\n");
    return 0;
}

SEC("kprobe/alloc_pipe_info+0x1a8")
int BPF_KPROBE(alloc_pipe_info_0x1a8){
    BPF_SET_R12(ctx, 0x3);
    bpf_printk("0x1a8\n");
    return 0;
}