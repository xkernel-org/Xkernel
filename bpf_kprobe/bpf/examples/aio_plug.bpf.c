// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"


/* __ia32_sys_io_submit */
SEC("kprobe/__ia32_sys_io_submit+0x75")
int BPF_KPROBE(__ia32_sys_io_submit_0x75){
    u64 r14 = BPF_R14(ctx);
    if(r14 > 0x3) {
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x75\n");
    }
    return 0;
}

SEC("kprobe/__ia32_sys_io_submit+0xc8")
int BPF_KPROBE(__ia32_sys_io_submit_0xc8){
    u64 r14 = BPF_R14(ctx);
    if(r14 <= 0x3) {
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0xc8\n");
    }
    return 0;
}

/* __ia32_compat_sys_io_submit */
SEC("kprobe/__ia32_compat_sys_io_submit+0x6e")
int BPF_KPROBE(__ia32_compat_sys_io_submit_0x6e){
    u32 r12d = (u32)(0xffffffff & BPF_R12(ctx));
    if(r12d > 0x3) {
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x6e\n");
    }
    return 0;
}

SEC("kprobe/__ia32_compat_sys_io_submit+0xbd")
int BPF_KPROBE(__ia32_compat_sys_io_submit_0xbd){
    u32 r12d = (u32)(0xffffffff & BPF_R12(ctx));
    if(r12d <= 0x3) {
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0xbd\n");
    }

    return 0;
}

/* __x64_sys_io_submit */
SEC("kprobe/__x64_sys_io_submit+0x6f")
int BPF_KPROBE(__x64_sys_io_submit_0x6f){
    u64 r13 = BPF_R13(ctx);
    if(r13 > 0x3) {
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x6f\n");
    }
    return 0;
}

SEC("kprobe/__x64_sys_io_submit+0xc1")
int BPF_KPROBE(__x64_sys_io_submit_0xc1){
    u64 r13 = BPF_R13(ctx);
    if(r13 <= 0x3) {
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0xc1\n");
    }
    return 0;
}