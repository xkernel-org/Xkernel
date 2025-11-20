// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/io_arm_poll_handler+0x176")
int BPF_KPROBE(io_arm_poll_handler_0x176){
    u64 r13 = BPF_R13(ctx);
    u64 *addr = (u64 *)(r13 + 0x14);
    u64 val = 0x100;

    kfuncs_probe_write_kernel(addr, sizeof(u64), &val, sizeof(u64));
    
    bpf_printk("0x175\n");
    return 0;
}