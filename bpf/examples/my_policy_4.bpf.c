// SPDX-License-Identifier: GPL-2.0
// Auto-generated for test group 4

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

// Kprobe 1a: tcp_rack_detect_loss+0x6a (SAVE — fires before shr executes)
SEC("kprobe/tcp_rack_detect_loss+0x6a")
int BPF_KPROBE(tcp_rack_detect_loss_0x6a_save) {
    if (!transition_done(ctx)) {
        return 0;
    }
    __u32 key = 0;
    __u64 val = BPF_R15(ctx);
    bpf_map_update_elem(&xk_save_0, &key, &val, BPF_ANY);
    return 0;
}

// Kprobe 1b: tcp_rack_detect_loss+0x6e (APPLY — fires after shr executes)
// Candidates: 0x6e
// Relationship: IV = V
SEC("kprobe/tcp_rack_detect_loss+0x6e")
int BPF_KPROBE(tcp_rack_detect_loss_0x6e) {
    if (!transition_done(ctx)) {
        return 0;
    }
    __u32 key = 0;
    __u64 *saved = bpf_map_lookup_elem(&xk_save_0, &key);
    if (!saved) return 0;

    // Get tunable value (V=2 originally)
    u64 v = 2; // TODO: Read from BPF map

    // Recompute: shr with new V — IV = V
    u64 result = *saved >> v;
    BPF_SET_R15(ctx, result);
    return 0;
}
