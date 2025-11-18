// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/update_task_scan_period+0x62")
int BPF_KPROBE(update_task_scan_period_0x62){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0x5){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x62\n");
    }
    bpf_printk("0x62\n");
    return 0;
}

SEC("kprobe/update_task_scan_period+0x6b")
int BPF_KPROBE(update_task_scan_period_0x6b){
    u64 eax = BPF_EAX(ctx);
    eax = eax + 1;
    BPF_SET_EAX(ctx,eax);
    bpf_printk("0x6b\n");
    return 0;
}

SEC("kprobe/update_task_scan_period+0x17e")
int BPF_KPROBE(update_task_scan_period_0x17e){
    u64 eax = BPF_EAX(ctx);
    if(eax <= 0x5){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x17e\n");
    }
    bpf_printk("0x17e\n");
    return 0; 
}

SEC("kprobe/update_task_scan_period+0x183")
int BPF_KPROBE(update_task_scan_period_0x183){
    u64 eax = BPF_EAX(ctx);
    eax = eax + 1;
    BPF_SET_EAX(ctx, eax);
    bpf_printk("0x183\n");
    return 0;
}

SEC("kprobe/update_task_scan_period+0x19e")
int BPF_KPROBE(update_task_scan_period_0x19e){
    u64 eax = BPF_EAX(ctx);
    eax = eax + 1;
    BPF_SET_EAX(ctx, eax);
    bpf_printk("0x19e\n");
    return 0;
}

SEC("kprobe/update_task_scan_period")
int BPF_KPROBE(update_task_scan_period_entry){
    bpf_printk("entry\n");
    return 0;
}