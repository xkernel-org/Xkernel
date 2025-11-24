// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/migrate_pages_sync+0x77")
int BPF_KPROBE(migrate_pages_sync_0x77){
    u64 rsp = BPF_RSP(ctx);
    u64 *addr = (u64 *)(rsp - 8);
    u64 val = 0x7;
    kfuncs_probe_write_kernel(addr, sizeof(u64), &val, sizeof(u64));
    bpf_printk("0x77\n");
    return 0;
}

SEC("kprobe/migrate_pages_sync+0x114")
int BPF_KPROBE(migrate_pages_sync_0x114){
    u64 rsp = BPF_RSP(ctx);
    u64 *addr = (u64 *)(rsp - 8);
    u64 val = 0x3;
    kfuncs_probe_write_kernel(addr, sizeof(u64), &val, sizeof(u64));
    bpf_printk("0x114\n");
    return 0;
}