// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/rcu_init_geometry+0x99")
int BPF_KPROBE(rcu_init_geometry_0x99){
    u64 eax = BPF_EAX(ctx);
    BPF_SET_EAX(ctx, eax << 1);
    bpf_printk("0x99\n");
    return 0;
}