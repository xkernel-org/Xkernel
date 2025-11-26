// SPDX-License-Identifier: GPL-2.0
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "xkernel.bpf.h"  

volatile __u64 g_total_hits;       
volatile __u64 g_last_print_ns;    

#define INTERVAL_NS (5ull * 1000 * 1000 * 1000) 

SEC("kprobe/do_shrink_slab+0xb")
int BPF_KPROBE(do_shrink_slab_0xb)
{
    __sync_fetch_and_add(&g_total_hits, 1);

    __u64 now = bpf_ktime_get_ns();
    if (now - g_last_print_ns >= INTERVAL_NS) {
        g_last_print_ns = now;  
        bpf_printk("do_shrink_slab(+0xb) total hits=%llu", g_total_hits);
    }

    // 256

    // 192

    // 160

    // 128 -- default

    // 96

    // 64 -- 0x40
    // BPF_SET_EAX(ctx, 0x40);

    // 32 -- 0x20
    // BPF_SET_EAX(ctx, 0x20);

    // 28 -- 0x1c
    // BPF_SET_EAX(ctx, 0x1c);

    // 27 -- 0x1b
    // BPF_SET_EAX(ctx, 0x1b);

    // 26 -- 0x1a
    // BPF_SET_EAX(ctx, 0x1a);

    // 25 -- 0x19
    // BPF_SET_EAX(ctx, 0x19);

    // 24 -- 0x18
    // BPF_SET_EAX(ctx, 0x18);

    // 23 -- 0x17
    // BPF_SET_EAX(ctx, 0x17);

    // 22 -- 0x16
    // BPF_SET_EAX(ctx, 0x16);

    // 20 -- 0x14
    // BPF_SET_EAX(ctx, 0x14);

    // 18 -- 0x12
    // BPF_SET_EAX(ctx, 0x12);

    // 16 -- 0x10
    // BPF_SET_EAX(ctx, 0x10);

    // 12 -- 0xc
    // BPF_SET_EAX(ctx, 0xc);

    // 8  -- 0x8
    BPF_SET_EAX(ctx, 0x8);

    // 1 -- 0x1
    // BPF_SET_EAX(ctx, 0x1);
   

    return 0;
}

// char LICENSE[] SEC("license") = "GPL";


/*
// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/do_shrink_slab+0xb")
int BPF_KPROBE(do_shrink_slab_0xb){

    // 256

    // 192

    // 160

    // 128 -- default

    // 96

    // 64 -- 0x40
    // BPF_SET_EAX(ctx, 0x40);

    // 32 -- 0x20
    // BPF_SET_EAX(ctx, 0x20);

    // 28 -- 0x1c
    // BPF_SET_EAX(ctx, 0x1c);

    // 27 -- 0x1b
    // BPF_SET_EAX(ctx, 0x1b);

    // 26 -- 0x1a
    // BPF_SET_EAX(ctx, 0x1a);

    // 25 -- 0x19
    // BPF_SET_EAX(ctx, 0x19);

    // 24 -- 0x18
    // BPF_SET_EAX(ctx, 0x18);

    // 23 -- 0x17
    // BPF_SET_EAX(ctx, 0x17);

    // 22 -- 0x16
    // BPF_SET_EAX(ctx, 0x16);

    // 20 -- 0x14
    // BPF_SET_EAX(ctx, 0x14);

    // 18 -- 0x12
    // BPF_SET_EAX(ctx, 0x12);

    // 16 -- 0x10
    BPF_SET_EAX(ctx, 0x10);

    // 12 -- 0xc
    // BPF_SET_EAX(ctx, 0xc);

    // 8  -- 0x8
    // BPF_SET_EAX(ctx, 0x8);

    // 1 -- 0x1
    // BPF_SET_EAX(ctx, 0x1);
    return 0;
}
*/

