// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "util.bpf.h"
#include "kfuncs.bpf.h"

char LICENSE[] SEC("license") = "GPL";

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

    u32 new_value = 256;
    kfuncs_probe_write_kernel(&q->nr_requests, sizeof(new_value), &new_value, sizeof(new_value));

    if (bpf_probe_read_kernel(&nr_requests, sizeof(nr_requests), &q->nr_requests) == 0) {
        bpf_printk("After hacking: nr_requests: %u", nr_requests);
    } else {
        bpf_printk("Failed to read nr_requests");
    }


    return 0;
}
