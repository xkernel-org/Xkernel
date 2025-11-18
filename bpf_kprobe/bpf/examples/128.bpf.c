// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/should_numa_migrate_memory+0x347")
int BPF_KPROBE(should_numa_migrate_memory_0x347){
    u64 rax = BPF_RAX(ctx);
    rax = (rax / 4) * 5;
    BPF_SET_RAX(ctx, rax);
    bpf_printk("0x347\n");
    return 0;
}