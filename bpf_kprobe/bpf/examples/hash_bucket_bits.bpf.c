// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/ext4_xattr_create_cache+0xb")
int BPF_KPROBE(ext4_xattr_create_cache_0xb){
    BPF_SET_EDI(ctx, 0x5);
    bpf_printk("0xb\n");
    return 0;
}

SEC("kprobe/ext4_xattr_create_cache")
int BPF_KPROBE(ext4_xattr_create_cache_entry){
    bpf_printk("entry\n");
    return 0;
}