// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/bh_worker+0xb2")
int BPF_KPROBE(bh_worker_0xb2){
    BPF_SET_R13(ctx, 0x14);
    bpf_printk("0xb2\n");
    return 0;
}