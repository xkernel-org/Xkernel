// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/io_poll_remove_all+0xec")
int BPF_KPROBE(io_poll_remove_all_0xec){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0xff){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0xec\n");
    }
    bpf_printk("0xec\n");
    return 0;
}

SEC("kprobe/io_poll_cancel+0xf2")
int BPF_KPROBE(io_poll_cancel_0xf2){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0xff){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0xf2\n");
    }
    bpf_printk("0xf2\n");
    return 0;
}

SEC("kprobe/io_poll_wake+0x49")
int BPF_KPROBE(io_poll_wake_0x49){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0xff){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x49\n");
    }
    bpf_printk("0x49\n");
    return 0;
}

SEC("kprobe/io_poll_can_finish_inline+0x39")
int BPF_KPROBE(io_poll_can_finish_inline_0x39){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0xff){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x39\n");
    }
    bpf_printk("0x39\n");
    return 0;
}

SEC("kprobe/io_poll_remove+0x86")
int BPF_KPROBE(io_poll_remove_0x86){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0xff){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x86\n");
    }
    bpf_printk("0x86\n");
    return 0;
}