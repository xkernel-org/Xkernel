// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// set_initial_priority.part.0
SEC("kprobe/set_initial_priority.part.0+0x6d")
int BPF_KPROBE(set_initial_priority_part_0_0x6d){
    BPF_SET_EDX(ctx, 0x5);
    bpf_printk("0x6d\n");
    return 0;
}

SEC("kprobe/set_initial_priority.part.0+0x77")
int BPF_KPROBE(set_initial_priority_part_0_0x77){
    BPF_SET_EDX(ctx, 0xb);
    bpf_printk("0xb\n");
    return 0;
}


// try_to_shrink_lruvec
SEC("kprobe/try_to_shrink_lruvec+0x1fe")
int BPF_KPROBE(try_to_shrink_lruvec_0x1fe){
    u64 eax = BPF_EAX(ctx);
    u64 *addr = (u64 *)(eax + 0x34);
    u64 val;
    bpf_probe_read_kernel(&val, sizeof(val), addr);

    if((val & 0xff) == 0xb){
        BPF_SET_JE_TRUE(ctx);
        bpf_printk("0x1fe\n");
    }
    bpf_printk("0x1fe\n");
    return 0;
}

SEC("kprobe/try_to_shrink_lruvec+0x28c")
int BPF_KPROBE(try_to_shrink_lruvec_0x28c){
    u64 eax = BPF_EAX(ctx);
    eax = eax & 0xff;

    if(eax == 0xb){
        BPF_SET_JE_TRUE(ctx);
        bpf_printk("0x28c\n");
    }
    bpf_printk("0x28c\n");
    return 0;
}

SEC("kprobe/try_to_shrink_lruvec+0x324")
int BPF_KPROBE(try_to_shrink_lruvec_0x324){
    BPF_SET_EBX(ctx, 0xb);
    bpf_printk("0x324\n");
    return 0;
}


// shrink_lruvec
SEC("kprobe/shrink_lruvec+0x454")
int BPF_KPROBE(shrink_lruvec_0x454){
    /*
    uint8_t val = *(uint8_t*)(rbx + 0x34);
    uint8_t result = (val == 12) ? 1 : 0;
    *(uint8_t*)(rsp + 0x27) = result;
    */

    u64 rbx = BPF_RBX(ctx);
    u64 *addr = (u64 *)(rbx + 0x34);
    u64 val;
    bpf_probe_read_kernel(&val, sizeof(val), addr);

    u64 rsp = BPF_RSP(ctx);
    u8 *dst = (u8 *)(rsp + 0x27);
    u8 dst_val = 1;

    if((val & 0xff) == 0xb){
        kfuncs_probe_write_kernel(dst, sizeof(u8), &dst_val, sizeof(u8));
        bpf_printk("0x454\n");
    }
    else{
        dst_val = 0;
        kfuncs_probe_write_kernel(addr, sizeof(u64), &dst_val, sizeof(u64)); 
        bpf_printk("0x454\n");
    }
    bpf_printk("0x454\n");
    return 0;
}


// shrink_node
SEC("kprobe/shrink_node+0x2da")
int BPF_KPROBE(shrink_node_0x2da){
    u64 r14 = BPF_R14(ctx);
    u64 *addr = (u64 *)(r14 + 0x34);
    u64 val;
    bpf_probe_read_kernel(&val, sizeof(val), addr);

    if(val <= 0x8){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x2da\n");
    }
    bpf_printk("0x2da\n");
    return 0;
}

SEC("kprobe/shrink_node+0x452")
int BPF_KPROBE(shrink_node_0x452){
    u64 r14 = BPF_R14(ctx);
    u64 *addr = (u64 *)(r14 + 0x34);
    u64 val;
    bpf_probe_read_kernel(&val, sizeof(val), addr);

    if(val != 0xb){
        BPF_SET_JNE_TRUE(ctx);
        bpf_printk("0x452\n");
    }
    bpf_printk("0x452\n");
    return 0;
}


// balance_pgdat
SEC("kprobe/balance_pgdat+0x173")
int BPF_KPROBE(balance_pgdat_0x173){
    u64 rbp = BPF_RBP(ctx);
    u8 *addr = (u8 *)(rbp - 0xa4);
    u8 val = 0xb;
    kfuncs_probe_write_kernel(addr, sizeof(u8), &val, sizeof(u8)); 
    bpf_printk("0x173\n");
    return 0;
}

SEC("kprobe/balance_pgdat+0x22d")
int BPF_KPROBE(balance_pgdat_0x22d){
    u64 rbp = BPF_RBP(ctx);
    u8 *addr = (u8 *)(rbp - 0xa4);
    u8 val;
    bpf_probe_read_kernel(&val, sizeof(val), addr);
    if(val > 0x8){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x22d\n");
    }
    bpf_printk("0x22d\n");
    return 0;
}

SEC("kprobe/balance_pgdat+0x4a8")
int BPF_KPROBE(balance_pgdat_0x4a8){
    /*
    --- (+0x4a1)ffffffff99d1a471:       80 bd 5c ff ff ff 0a    cmpb   $0xa,-0xa4(%rbp)
    ---   cmpb   $0xb,-0xa4(%rbp)
    (+0x4a8)ffffffff99d1a478:       0f 95 85 08 ff ff ff    setne  -0xf8(%rbp)
    */ 

    u64 rbp = BPF_RBP(ctx);
    u64 *addr = (u64 *)(rbp - 0xa4);
    u64 val;
    bpf_probe_read_kernel(&val, sizeof(val), addr);

    u8 *dst = (u8 *)(rbp - 0xf8);
    u8 dst_val = 1;

    if((val & 0xff) != 0xb){
        kfuncs_probe_write_kernel(dst, sizeof(u8), &dst_val, sizeof(u8));
        bpf_printk("0x4a8\n");
    }
    else{
        dst_val = 0;
        kfuncs_probe_write_kernel(addr, sizeof(u64), &dst_val, sizeof(u64)); 
        bpf_printk("0x4a8\n");
    }
    bpf_printk("0x4a8\n");
    return 0;
}


// do_try_to_free_pages
SEC("kprobe/do_try_to_free_pages+0x172")
int BPF_KPROBE(do_try_to_free_pages_0x172){
    u8 al = (BPF_EAX(ctx) & 0xff);
    if(al <= 0x8){
        BPF_SET_JLE_TRUE(ctx);
        bpf_printk("0x172");
    }
    bpf_printk("0x172");
    return 0;
}


// try_to_free_pages
SEC("kprobe/try_to_free_pages+0x6c")
int BPF_KPROBE(try_to_free_pages_0x6c){
    u64 rbp = BPF_RBP(ctx);
    u8 *addr = (u8 *)(rbp - 0x74);
    u8 val = 0xb;
    kfuncs_probe_write_kernel(addr, sizeof(u8), &val, sizeof(u8));
    bpf_printk("0x6c\n");
    return 0;
}


// try_to_free_mem_cgroup_pages
SEC("kprobe/try_to_free_mem_cgroup_pages+0x94")
int BPF_KPROBE(try_to_free_mem_cgroup_pages_0x94){
    BPF_SET_ESI(ctx, 0x40b);
    bpf_printk("0x94\n");
    return 0;
}


// shrink_all_memory
SEC("kprobe/shrink_all_memory+0x51")
int BPF_KPROBE(shrink_all_memory_0x51){
    BPF_SET_RAX(ctx, 0x40b00002070);
    bpf_printk("0x4e\n");
    return 0;
}
