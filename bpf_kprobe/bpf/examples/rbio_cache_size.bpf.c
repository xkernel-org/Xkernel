// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/unlock_stripe+0x282")
int BPF_KPROBE(unlock_stripe_0x282){
    u64 r15 = BPF_R15(ctx);
    u64 *addr = (u64 *)(r15 + 0x14);
    u64 value;
    bpf_probe_read_kernel(&value, sizeof(u64), addr);

    if(value <= 0x200){
        BPF_SET_JLE_TRUE(ctx);
        // bpf_printk("0x282\n");
    }
    bpf_printk("0x282\n");
    return 0;
}