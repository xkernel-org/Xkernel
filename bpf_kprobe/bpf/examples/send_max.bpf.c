// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/check_extent_item+0x31")
int BPF_KPROBE(check_extent_item_0x31){
    u64 r14 = BPF_R14(ctx);
    if(r14 > 0x200){
        BPF_SET_JA_TRUE(ctx);
        bpf_printk("0x38\n");
    }
    bpf_printk("0x38\n");
    return 0;
}