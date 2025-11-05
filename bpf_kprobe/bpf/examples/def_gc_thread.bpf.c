// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/f2fs_start_gc_thread+0x78")

int BPF_KPROBE(f2fs_start_gc_thread_0x78){
    u64 rax = BPF_RAX(ctx);
    u64 *addr = (u64 *)(rax + 0x20);
    u64 value = 0x64;
    kfuncs_probe_write_kernel(addr, sizeof(u64), &value, sizeof(u64));
    bpf_printk("0x78\n");
    return 0;
}