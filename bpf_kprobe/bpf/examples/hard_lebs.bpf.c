// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/ubifs_garbage_collect+0x12e")
int BPF_KPROBE(ubifs_garbage_collect_0x12e){
    u64 r12 = BPF_R12(ctx);
    if(r12 == 0x11){
        BPF_SET_JE_TRUE(ctx);
        bpf_printk("0x12e\n");
    }
    bpf_printk("0x12e\n");
    return 0;
}