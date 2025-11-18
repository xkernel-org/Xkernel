// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/do_shrink_slab+0xac")
int BPF_KPROBE(do_shrink_slab_0xac){
    u64 rax = BPF_RAX(ctx);
    rax = rax >> 1;
    BPF_SET_RAX(ctx, rax);
    bpf_printk("0xac\n");
    return 0;
}