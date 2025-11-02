// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/mb_cache_entry_create+0x20d")
int BPF_KPROBE(mb_cache_entry_create_0x20d){
    BPF_SET_ESI(ctx, 0x20);
    bpf_printk("0x20d\n");
    return 0;
}

/*
SEC("kprobe/mb_cache_entry_create")
int BPF_KPROBE(mb_cache_entry_create_entry){
    bpf_printk("entry\n");
    return 0;
}
*/