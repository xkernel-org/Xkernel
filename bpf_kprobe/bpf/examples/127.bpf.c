// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/task_numa_work+0x8c8")
int BPF_KPROBE(task_numa_work_0x8c8){
    u64 eax = BPF_EAX(ctx);
    eax = eax << 1;
    BPF_SET_EAX(ctx, eax);
    bpf_printk("0x8c8\n");
    return 0;
}