// SPDX-License-Identifier: GPL-2.0
// Auto-generated SIE indirection for test group 4
#ifndef __MY_POLICY_4_INTERNAL_H__
#define __MY_POLICY_4_INTERNAL_H__

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "cs_artifact.bpf.h"

// Per-CPU input-save map for kprobe 0 (irreversible synthesis)
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} xk_save_0 SEC(".maps");

// SIE helper 0: irreversible (shr) -> %r15d
static __always_inline void __sie_4_0(struct pt_regs *regs, u64 val) {
    __u32 key = 0;
    __u64 *saved = bpf_map_lookup_elem(&xk_save_0, &key);
    if (!saved) return;
    u64 result = *saved >> val;
    sie_write_kernel(&regs->r15, sizeof(regs->r15), &result);
}

// Save handler 0: tcp_rack_detect_loss+0x6a (fires BEFORE shr)
SEC("kprobe/tcp_rack_detect_loss+0x6a")
int BPF_KPROBE(__xk_save_4_0_tcp_rack_detect_loss) {
    if (!transition_done(ctx)) return 0;
    __u32 key = 0;
    __u64 val = BPF_R15(ctx);
    bpf_map_update_elem(&xk_save_0, &key, &val, BPF_ANY);
    return 0;
}

#define X_TUNE_0(func_name, location_str) \
    static int __xk_policy_4_0(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(__xk_4_0) { \
        struct x_ctx __x_ctx = { .regs = ctx, .set_fn = &__sie_4_0 }; \
        return __xk_policy_4_0(&__x_ctx, ctx); \
    } \
    static int __xk_policy_4_0(struct x_ctx *x_ctx, struct pt_regs *ctx)

#endif // __MY_POLICY_4_INTERNAL_H__
