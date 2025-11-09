// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/sched_balance_rq+0x788")
int BPF_KPROBE(sched_balance_rq_0x788){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0xff){
        BPF_SET_JA_TRUE(ctx);
        bpf_printk("0x788\n");
    }
    bpf_printk("0x788\n");
    return 0;
}