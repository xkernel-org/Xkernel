// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"


// f2fs_compress_pages
SEC("kprobe/f2fs_compress_pages+0x112")
int BPF_KPROBE(f2fs_compress_pages_0x112){
    BPF_SET_EBX(ctx, 0x2);
    bpf_printk("0x112\n");
    return 0;
}

SEC("kprobe/f2fs_compress_pages+0x2d5")
int BPF_KPROBE(f2fs_compress_pages_0x2d5){
    BPF_SET_EBX(ctx, 0x2);
    bpf_printk("0x112\n");
    return 0;
}


// f2fs_prepare_decomp_mem
SEC("kprobe/f2fs_prepare_decomp_mem+0x11f")
int BPF_KPROBE(f2fs_prepare_decomp_mem_0x11f){
    BPF_SET_R14(ctx, 0x2);
    bpf_printk("0x11f\n");
    return 0;
}

SEC("kprobe/f2fs_prepare_decomp_mem+0x16f")
int BPF_KPROBE(f2fs_prepare_decomp_mem_0x16f){
    BPF_SET_R12(ctx, 0x2);
    bpf_printk("0x16f\n");
    return 0;
}

