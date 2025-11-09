// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/task_numa_find_cpu+0x47")
int BPF_KPROBE(task_numa_find_cpu_0x47){
    u64 edx = BPF_EDX(ctx);
    if(edx <= 0x3){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x47\n");
    }
    bpf_printk("0x47\n");
    return 0;
}


SEC("kprobe/sched_balance_find_dst_group+0x44e")
int BPF_KPROBE(sched_balance_find_dst_group_0x44e){
    u64 edx = BPF_EDX(ctx);
    if(edx > 0x3){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x44e\n");
    }
    bpf_printk("0x44e\n");
    return 0;
}



SEC("kprobe/sched_balance_find_src_group+0x71")
int BPF_KPROBE(sched_balance_find_src_group_0x71){
    u64 r13 = BPF_R13(ctx);
    if(r13 == 0x3){
        BPF_SET_JE_TRUE(ctx);
        bpf_printk("0x71\n");
    }
    bpf_printk("0x71\n");
    return 0;
}

// auto trigger