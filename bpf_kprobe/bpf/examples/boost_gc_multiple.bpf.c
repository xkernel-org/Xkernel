// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/do_garbage_collect+0x822")
int BPF_KPROBE(do_garbage_collect_0x822){
    u64 r9 = BPF_R9(ctx);
    r9 = (r9 / 5) * 4;
    BPF_SET_R9(ctx, r9);
    bpf_printk("0x822\n"); 
    return 0;
}