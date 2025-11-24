// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/migrate_hugetlbs+0x11a")
int BPF_KPROBE(migrate_hugetlbs_0x11a){
    u64 eax = BPF_EAX(ctx);
    if(eax == 0x13){
        BPF_SET_JE_TRUE(ctx);
        bpf_printk("0x11a\n");
    }
    bpf_printk("0x11a\n");
    return 0;
}

SEC("kprobe/migrate_pages+0x1a4")
int BPF_KPROBE(migrate_pages_0x1a4){
    u64 rsp = BPF_RSP(ctx);
    u64 *addr = (u64 *)(rsp - 8);
    u64 val = 0x14;
    kfuncs_probe_write_kernel(addr, sizeof(u64), &val, sizeof(u64));
    bpf_printk("0x1a4\n");
    return 0;
}

SEC("kprobe/migrate_pages_sync+0x114")
int BPF_KPROBE(migrate_pages_sync_0x114){
    u64 rsp = BPF_RSP(ctx);
    u64 *addr = (u64 *)(rsp - 8);
    u64 val = 0x11;
    kfuncs_probe_write_kernel(addr, sizeof(u64), &val, sizeof(u64)); 
    bpf_printk("0x114\n");
    return 0;
}


