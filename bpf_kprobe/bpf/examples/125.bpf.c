// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/task_numa_work+0x10a")
int BPF_KPROBE(task_numa_work_0x10a){
    /*
    --- addq   $0x1e8480,0x1030(%r12)
    --- addq   $0x2dc6c0,0x1030(%r12)
    */
    u64 r12 = BPF_R12(ctx);
    u64 *addr = (u64 *)(r12 + 0x1030);
    u64 origin_val, target_val;

    bpf_probe_read_kernel(&origin_val, sizeof(origin_val), addr);
    target_val = origin_val + (0x2dc6c0 - 0x1e8480);
    kfuncs_probe_write_kernel(addr, sizeof(u64), &target_val, sizeof(u64));

    bpf_printk("0x10a\n");
    return 0;
}