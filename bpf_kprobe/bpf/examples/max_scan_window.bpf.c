// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"


// task_scan_start
SEC("kprobe/task_scan_start+0x25")
int BPF_KPROBE(task_scan_start_0x25){
    u64 ecx = BPF_ECX(ctx);
    if(ecx > 0x4ff){
        BPF_SET_JA_TRUE(ctx);
        bpf_printk("0x25\n");
    }
    bpf_printk("0x25\n");
    return 0;
}

SEC("kprobe/task_scan_start+0x2c")
int BPF_KPROBE(task_scan_start_0x2c){
    BPF_SET_EAX(ctx, 0x500);
    bpf_printk("0x2c\n");
    return 0;
}


// task_scan_max
SEC("kprobe/task_scan_max+0x27")
int BPF_KPROBE(task_scan_max_0x27){
    u64 ecx = BPF_ECX(ctx);
    if(ecx > 0x4ff){
        BPF_SET_JA_TRUE(ctx);
        bpf_printk("0x27\n");
    }
    bpf_printk("0x27\n");
    return 0;
}

SEC("kprobe/task_scan_max+0x2e")
int BPF_KPROBE(task_scan_max_0x2e){
    BPF_SET_EAX(ctx, 0x500);
    bpf_printk("0x2e\n");
    return 0;
}


// update_task_scan_period
// task_scan_max
SEC("kprobe/update_task_scan_period+0x8e")
int BPF_KPROBE(update_task_scan_period_0x8e){
    u64 ecx = BPF_ECX(ctx);
    if(ecx > 0x4ff){
        BPF_SET_JA_TRUE(ctx);
        bpf_printk("0x8e\n");
    }
    bpf_printk("0x8e\n");
    return 0;
}

SEC("kprobe/update_task_scan_period+0x95")
int BPF_KPROBE(update_task_scan_period_0x95){
    BPF_SET_EAX(ctx, 0x500);
    bpf_printk("0x95\n");
    return 0;
}

// auto trigger


