// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/pcpu_alloc_noprof+0x1e5")
int BPF_KPROBE(pcpu_alloc_noprof_0x1e5){
    // 3 -> 5
    //  (+0x1e1)ffffffffb2335e31:       83 7d c8 02             cmpl   $0x2,-0x38(%rbp)
    //                                                          cmpl   $0x4,-0x38(%rbp)
    //  (+0x1e5)ffffffffb2335e35:       7f cc                   jg     0xffffffffb2335e03
    u64 *addr;
    addr = (u64 *)(BPF_RBP(ctx) - 0x38);
    u64 value = bpf_probe_read_kernel(&value, sizeof(u64), addr);
    if(value >= 0x1) {
        bpf_printk("0x1e5\n");
        BPF_SET_JG_TRUE(ctx);
    }
    return 0;
}
