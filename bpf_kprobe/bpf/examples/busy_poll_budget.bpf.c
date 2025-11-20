// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"


SEC("kprobe/io_napi_sqpoll_busy_poll+0xdd")
int BPF_KPROBE(io_napi_sqpoll_busy_poll_0xdd){
    BPF_SET_R8(ctx, 0x20);
    bpf_printk("0xdd\n");
    return 0;
}

SEC("kprobe/__io_napi_busy_loop+0x113")
int BPF_KPROBE(__io_napi_busy_loop_0x113){
    BPF_SET_R8(ctx, 0x20);
    bpf_printk("0x113\n");
    return 0;
}

SEC("kprobe/dynamic_tracking_do_busy_loop+0x63")
int BPF_KPROBE(dynamic_tracking_do_busy_loop_0x63){
    BPF_SET_R8(ctx, 0x20);
    bpf_printk("0x63\n");
    return 0;
}

SEC("kprobe/ep_poll+0x1bb")
int BPF_KPROBE(ep_poll_0x1bb){
    BPF_SET_ESI(ctx, 0x20);
    bpf_printk("0x1bb\n");
    return 0;
}