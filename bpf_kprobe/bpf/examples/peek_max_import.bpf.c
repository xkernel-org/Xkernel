// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"


SEC("kprobe/io_ring_buffers_peek+0xa8")
int BPF_KPROBE(io_ring_buffers_peek_0xa8){
    BPF_SET_EDX(ctx, 0x80);
    bpf_printk("0xa8\n");
    return 0;
}

SEC("kprobe/io_ring_buffers_peek+0x2c1")
int BPF_KPROBE(io_ring_buffers_peek_0x2c1){
    BPF_SET_EAX(ctx, 0x80);
    bpf_printk("0x2c1\n");
    return 0;
}