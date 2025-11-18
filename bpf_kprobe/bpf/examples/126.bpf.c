// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/should_numa_migrate_memory+0x273")
int BPF_KPROBE(should_numa_migrate_memory_0x273){
    u64 r15 = BPF_R15(ctx);
    u64 *addr = (u64 *)(r15 + 0x1010);
    u64 val;
    bpf_probe_read_kernel(&val, sizeof(val), addr);

    if(val <= 0x6){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x273\n");
    }
    bpf_printk("0x273\n");
    return 0;
}