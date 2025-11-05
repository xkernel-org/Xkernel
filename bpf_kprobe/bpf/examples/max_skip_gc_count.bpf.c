// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/f2fs_gc+0x879")
int BPF_KPROBE(f2fs_gc_0x879){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 8){
        BPF_SET_JBE_TRUE(ctx);
        bpf_printk("0x879\n");
    }
    return 0;
}
