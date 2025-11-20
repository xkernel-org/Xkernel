// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/io_uring_fill_params+0x22")
int BPF_KPROBE(io_uring_fill_params_0x22){
    u64 edi = BPF_EDI(ctx);
    if(edi <= 0x4000){
        BPF_SET_JBE_TRUE(ctx);
        bpf_printk("0x22\n");
    }
    bpf_printk("0x22\n");
    return 0;
}

SEC("kprobe/io_uring_fill_params+0x32")
int BPF_KPROBE(io_uring_fill_params_0x32){
    BPF_SET_EDI(ctx, 0x4000);
    bpf_printk("0x32\n");
    return 0;
}