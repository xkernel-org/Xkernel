// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

/*
SEC("kprobe/io_recv_finish+0x3b5")
int BPF_KPROBE(io_recv_finish_0x3b5){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0xf){
        BPF_SET_JA_TRUE(ctx);
        bpf_printk("0x3b5\n");
    }
    bpf_printk("0x3b5\n");
    return 0;
}/
*/

SEC("kprobe/io_recv_finish")
int BPF_KPROBE(io_recv_finish){
    bpf_printk("entry\n");
    return 0;
}