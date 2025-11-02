// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"


SEC("kprobe/select_estimate_accuracy+0xda")
int BPF_KPROBE(select_estimate_accuracy_0xda){
    u64 rdx = BPF_RDX(ctx);
    rdx = rdx - 0x32;
    BPF_SET_RDX(ctx, rdx);
    bpf_printk("0xda\n");
    return 0;
}

SEC("kprobe/select_estimate_accuracy+0xed")
int BPF_KPROBE(select_estimate_accuracy_0xed){
    BPF_SET_EDX(ctx, 0x2faf080);
    bpf_printk("0xed\n");
    return 0;
}

SEC("kprobe/select_estimate_accuracy+0x119")
int BPF_KPROBE(select_estimate_accruacy_0x119){
    BPF_SET_EAX(ctx, 0x2faf080);
    bpf_printk("0x119\n");
    return 0;
}