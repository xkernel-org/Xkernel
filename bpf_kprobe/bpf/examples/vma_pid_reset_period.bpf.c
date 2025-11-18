// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/task_numa_work+0x2da")
int BPF_KPROBE(task_numa_work_0x2da){
    u64 edi = BPF_EDI(ctx);
    edi = edi / 4 * 2;
    BPF_SET_EDI(ctx, edi);
    bpf_printk("0x2da\n"); 
    return 0;
}

SEC("kprobe/task_numa_work+0x7f1")
int BPF_KPROBE(task_numa_work_0x7fa){
    u64 edi = BPF_EDI(ctx);
    edi = edi / 4 * 2;
    BPF_SET_EDI(ctx, edi);
    bpf_printk("0x7f1\n"); 
    return 0;
}