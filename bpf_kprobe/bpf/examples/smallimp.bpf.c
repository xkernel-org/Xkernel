// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/task_numa_compare+0x3df")
int BPF_KPROBE(task_numa_compare_0x3df){
    u64 r12 = BPF_R12(ctx);
    if(r12 <= 0x1e){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x3df\n");
    }
    bpf_printk("0x3df\n");
    return 0;
}