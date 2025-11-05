// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/__get_node_page.part.0+0x6f")
int BPF_KPROBE(__get_node_page_part_0_0x6f){
    BPF_SET_EDX(ctx, 0x40);
    bpf_printk("0x6f\n"); 
    return 0;
}

/*
SEC("kprobe/__get_node_page")
int BPF_KPROBE(__get_node_page_part_entry){
    bpf_printk("entry\n");
    return 0;
}
*/