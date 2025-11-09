// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/bh_worker+0xac")
int BPF_KPROBE(bh_worker_0xac){
    u64 r13 = BPF_R13(ctx);
    BPF_SET_EAX(ctx, r13 + 0x1);
    bpf_printk("0xac\n");
    return 0;
}