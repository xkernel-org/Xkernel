// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "cs_artifact.bpf.h"

SEC("kprobe/io_poll_remove_all+0xd9")
int BPF_KPROBE(io_poll_remove_all_0xd9){
    if (!transition_done(ctx)) {
        return 0;
    }
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0x7f){
        BPF_SET_JLE_TRUE(ctx);
    }
    bpf_printk("0xd9");
    return 0;
}

SEC("kprobe/io_poll_wake+0x49")
int BPF_KPROBE(io_poll_wake_0x49){
    if (!transition_done(ctx)) {
        return 0;
    }
    u64 eax = BPF_EAX(ctx);
    if(eax > 0x7f){
        BPF_SET_JG_TRUE(ctx);
    }
    bpf_printk("0x49");
    return 0;
}

SEC("kprobe/io_poll_cancel+0xbf")
int BPF_KPROBE(io_poll_cancel_0xbf){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0x7f){
        BPF_SET_JG_TRUE(ctx);
    }
    bpf_printk("0xbf");
    return 0;
}

SEC("kprobe/io_poll_wake+0xf0")
int BPF_KPROBE(io_poll_wake_0xf0){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0x7f){
        BPF_SET_JG_TRUE(ctx);
    }
    bpf_printk("0xf0");
    return 0;
}

SEC("kprobe/io_poll_can_finish_inline+0x39")
int BPF_KPROBE(io_poll_can_finish_inline_0x39){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0x7f){
        BPF_SET_JG_TRUE(ctx);
    }
    bpf_printk("0x39");
    return 0;
}

SEC("kprobe/io_poll_remove+0x88")
int BPF_KPROBE(io_poll_remove_0x88){
    u64 eax = BPF_EAX(ctx);
    if(eax > 0x7f){
        BPF_SET_JG_TRUE(ctx);
    }
    bpf_printk("0x88");
    return 0;
}