// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/__tlb_batch_free_encoded_pages+0x29")
int BPF_KPROBE(__tlb_batch_free_encoded_pages_0x29){
    // set to 0x800(2048)
    // set to 0x400(1024)
    BPF_SET_EBX(ctx, 0x400);
    bpf_printk("0x29\n");
    return 0;
}

SEC("kprobe/__tlb_batch_free_encoded_pages+0x8e")
int BPF_KPROBE(__tlb_batch_free_encoded_pages_0x8e){
    u64 eax = (u64)BPF_EAX(ctx);
    // set to 0x7ff(2047)
    // set to 0x3ff(1023)
    if(eax > 1023){ 
        BPF_SET_JA_TRUE(ctx); 
        bpf_printk("0x8e\n");
    }
    bpf_printk("0x8e\n");
    return 0;
}