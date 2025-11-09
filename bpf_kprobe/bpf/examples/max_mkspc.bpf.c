// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/make_free_space+0x14a")
int BPF_KPROBE(make_free_space_0x14a){
    u64 r14 = BPF_R14(ctx);
    if(r14 != 0x6){
        BPF_SET_JNE_TRUE(ctx);
    }
    bpf_printk("0x14a\n");
    return 0;
}