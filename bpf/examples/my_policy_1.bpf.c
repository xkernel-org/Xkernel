// SPDX-License-Identifier: GPL-2.0
// Auto-generated for test group 1

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "util.bpf.h"

// Per-CPU input-save map for kprobe 1 (irreversible synthesis)
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} xk_save_0 SEC(".maps");

// Kprobe 1a: cubictcp_acked+0x217 (SAVE — fires before shr executes)
SEC("kprobe/cubictcp_acked+0x217")
int BPF_KPROBE(cubictcp_acked_0x217_save) {
    if (!transition_done(ctx)) {
        return 0;
    }
    __u32 key = 0;
    __u64 val = BPF_RAX(ctx);
    bpf_map_update_elem(&xk_save_0, &key, &val, BPF_ANY);
    return 0;
}

// Kprobe 1b: cubictcp_acked+0x21a (APPLY — fires after shr executes)
// Candidates: 0x21a
// Relationship: IV = V
SEC("kprobe/cubictcp_acked+0x21a")
int BPF_KPROBE(cubictcp_acked_0x21a) {
    if (!transition_done(ctx)) {
        return 0;
    }
    __u32 key = 0;
    __u64 *saved = bpf_map_lookup_elem(&xk_save_0, &key);
    if (!saved) return 0;

    // Get tunable value (V=3 originally)
    u64 v = 3; // TODO: Read from BPF map

    // Recompute: shr with new V — IV = V
    u64 result = *saved >> v;
    BPF_SET_EAX(ctx, result);
    return 0;
}
