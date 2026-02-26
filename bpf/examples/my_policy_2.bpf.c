// SPDX-License-Identifier: GPL-2.0
// Auto-generated for test group 2

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "util.bpf.h"
#include "kfuncs.bpf.h"

// Kprobe 1: blk_mq_delay_run_hw_queue+0xc9 (memory store)
// Candidates: 0xc9
// Relationship: IV = V
SEC("kprobe/blk_mq_delay_run_hw_queue+0xc9")
int BPF_KPROBE(blk_mq_delay_run_hw_queue_0xc9) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Compute target address: rbx + 0xa4
    u64 addr = BPF_RBX(ctx) + 0xa4;

    // Get tunable value (V=8 originally)
    u64 val = 8; // TODO: Read from BPF map
    __u32 new_val = (__u32)val;

    // Overwrite memory (4 bytes)
    bpf_probe_write_kernel((void *)addr, sizeof(new_val), &new_val);
    return 0;
}

// Kprobe 2: blk_mq_map_swqueue+0x41e (memory store)
// Candidates: 0x41e
// Relationship: IV = V
SEC("kprobe/blk_mq_map_swqueue+0x41e")
int BPF_KPROBE(blk_mq_map_swqueue_0x41e) {
    if (!transition_done(ctx)) {
        return 0;
    }

    // Compute target address: r14 + 0xa4
    u64 addr = BPF_R14(ctx) + 0xa4;

    // Get tunable value (V=8 originally)
    u64 val = 8; // TODO: Read from BPF map
    __u32 new_val = (__u32)val;

    // Overwrite memory (4 bytes)
    bpf_probe_write_kernel((void *)addr, sizeof(new_val), &new_val);
    return 0;
}
