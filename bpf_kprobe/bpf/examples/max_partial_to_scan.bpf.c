// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/count_partial_free_approx+0x2a")
int BPF_KPROBE(count_partial_free_approx_0x2a){
    // 10000 -> 20000
    // 0x2710 -> 0x4e20
    // (+0x23)ffffffffb239dbc3:        49 81 f8 10 27 00 00    cmp    $0x2710,%r8
    // (+0x2a)ffffffffb239dbca:        77 7c                   ja     0xffffffffb239dc48
    u64 r8 = BPF_R8(ctx);
    if(r8 > 0x1388){
        bpf_printk("0x2a\n");
        BPF_SET_JA_TRUE(ctx);
    }
    bpf_printk("0x2a\n");
    return 0;
}


SEC("kprobe/count_partial_free_approx+0x103")
int BPF_KPROBE(count_partial_free_approx_0x103){
    // 10000 -> 20000
    // 0x1388 -> 0x2710
    // (+0xfc)ffffffffb239dc9c:        48 81 fe 88 13 00 00    cmp    $0x1388,%rsi
    // (+0x103)ffffffffb239dca3:       74 0d                   je     0xffffffffb239dcb2
    u64 rsi = BPF_RSI(ctx);
    if(rsi == 0x9c4){
        bpf_printk("0x103\n");
        BPF_SET_ZF_TRUE(ctx);
    }
    bpf_printk("0x103\n");
    return 0;
}


SEC("kprobe/count_partial_free_approx+0x190")
int BPF_KPROBE(count_partial_free_approx_0x190){
    // 10000 -> 20000
    // 0x2710 -> 0x4e20
    // (+0x189)ffffffffb239dd29:       48 81 fe 10 27 00 00    cmp    $0x2710,%rsi
    // (+0x190)ffffffffb239dd30:       75 ce                   jne    0xffffffffb239dd00
    u64 rsi = BPF_RSI(ctx);
    if(rsi != 0x1388){
        bpf_printk("0x190\n");
        BPF_SET_ZF_FALSE(ctx);
    }
    bpf_printk("0x190\n");
    return 0;
}

/*
SEC("kprobe/count_partial_free_approx")
int BPF_KPROBE(count_partial_free_approx_entry)
{
    bpf_printk("enter count_partial_free_approx()\n");
    return 0;
}
*/
