// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/io_task_refs_refill+0x17")
int BPF_KPROBE(io_task_refs_refill_0x17){
    BPF_SET_R12(ctx, 0x200);
    bpf_printk("0x17\n");
    return 0;
}