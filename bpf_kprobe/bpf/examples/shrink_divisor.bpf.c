// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/mb_cache_shrink_worker+0x12")
int BPF_KPROBE(mb_cache_shrink_worker_0x12){
    u64 rsi = BPF_RSI(ctx);

    rsi = rsi >> 4; 
    // rsi = rsi << 1; // 1 / 8

    BPF_SET_RSI(ctx, rsi);
    // bpf_printk("0x12\n");

    return 0;
}

