// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "util.bpf.h"
#include "kfuncs.bpf.h"

char LICENSE[] SEC("license") = "GPL";

const static int OLD_VALUE = 128;
const static int NEW_VALUE = 256;

SEC("kprobe/blk_alloc_queue+0x1be")
int BPF_KPROBE(assign_nr_requests)
{
    unsigned long pc = PT_REGS_IP(ctx);
    bpf_printk("current pc: %lx", pc);

    dump_ctx(ctx);
    
    // read value from 0x148(%rbx)
    u64 value = 0;
    if (bpf_probe_read_kernel(&value, sizeof(value), (void *)(ctx->bx + 0x148)) == 0) {
        bpf_printk("current value: %lx", value); 
    } else {
        bpf_printk("failed to read value");
    }

    return 0;
}

SEC("kretprobe/blk_alloc_queue")
int BPF_KRETPROBE(read_nr_requests)
{
    struct request_queue *q = (struct request_queue *)PT_REGS_RC(ctx);
    u32 nr_requests = 0;

    if (!q) {
        bpf_printk("q is NULL");
        return 0;
    }

    if (bpf_probe_read_kernel(&nr_requests, sizeof(nr_requests), &q->nr_requests) == 0) {
        bpf_printk("Before hacking: nr_requests: %u", nr_requests);
    } else {
        bpf_printk("Failed to read nr_requests");
    }

    u32 new_value = NEW_VALUE;
    kfuncs_probe_write_kernel(&q->nr_requests, sizeof(new_value), &new_value, sizeof(new_value));

    if (bpf_probe_read_kernel(&nr_requests, sizeof(nr_requests), &q->nr_requests) == 0) {
        bpf_printk("After hacking: nr_requests: %u", nr_requests);
    } else {
        bpf_printk("Failed to read nr_requests");
    }

    return 0;
}

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, u32);
    __type(value, u32);
} restore_map SEC(".maps");

SEC("kprobe/blk_mq_tag_update_depth+0x34")
int BPF_KPROBE(check_MAX_SCHED_RQ)
{
    unsigned long pc = PT_REGS_IP(ctx);
    bpf_printk("current pc: %lx", pc);

    u32 diff = 0;
    u32 *ptr = (u32 *)(ctx->bx);
    
    u32 key = 0;
    u32 *restore_v = bpf_map_lookup_elem(&restore_map, &key);
    if (!restore_v) {
        bpf_printk("failed to lookup restore_v");
        return 0;
    }

    u32 ptr_value;
    if (bpf_probe_read_kernel(&ptr_value, sizeof(ptr_value), ptr) != 0) {
        bpf_printk("failed to read ptr_value");
        return 0;
    }
    *restore_v = ptr_value;
    
    if (OLD_VALUE < NEW_VALUE) {
        diff = NEW_VALUE - OLD_VALUE;
        if (ptr_value > diff) {
            u32 t = ptr_value - diff;
            kfuncs_probe_write_kernel(ptr, sizeof(t), &t, sizeof(t));
        } else {
            u32 t = 0;
            kfuncs_probe_write_kernel(ptr, sizeof(t), &t, sizeof(t));
        }
    } else {
        diff = OLD_VALUE - NEW_VALUE;
        u32 t = ptr_value + diff;
        kfuncs_probe_write_kernel(ptr, sizeof(t), &t, sizeof(t));
    }

    return 0;
}

SEC("kprobe/blk_mq_tag_update_depth+0x3c")
int BPF_KPROBE(cont_check_MAX_SCHED_RQ)
{
    unsigned long pc = PT_REGS_IP(ctx);
    bpf_printk("continue: current pc: %lx", pc);

    u32 key = 0;
    u32 *restore_v = bpf_map_lookup_elem(&restore_map, &key);
    if (!restore_v) {
        bpf_printk("failed to lookup restore_v");
        return 0;
    }
    
    u32 *ptr = (u32 *)(ctx->bx);
    kfuncs_probe_write_kernel(ptr, sizeof(*ptr), restore_v, sizeof(*restore_v));

    return 0;
}

SEC("kprobe/blk_mq_tag_update_depth+0xa1")
int BPF_KPROBE(jump_check_MAX_SCHED_RQ)
{
    unsigned long pc = PT_REGS_IP(ctx);
    bpf_printk("jump: current pc: %lx", pc);
    
    u32 key = 0;
    u32 *restore_v = bpf_map_lookup_elem(&restore_map, &key);
    if (!restore_v) {
        bpf_printk("failed to lookup restore_v");
        return 0;
    }
    
    u32 *ptr = (u32 *)(ctx->bx);
    kfuncs_probe_write_kernel(ptr, sizeof(*ptr), restore_v, sizeof(*restore_v));
    
    return 0;
}