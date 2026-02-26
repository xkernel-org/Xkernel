// SPDX-License-Identifier: GPL-2.0
// Auto-generated SIE indirection for test group 6
#ifndef __MY_POLICY_6_INTERNAL_H__
#define __MY_POLICY_6_INTERNAL_H__

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// SIE helper 0: memory store -> mem[rbx+0xa4] (4B)
static __always_inline void __sie_6_0(struct pt_regs *regs, u64 val) {
    u64 addr = (u64)(regs->bx) + 0xa4;
    __u32 new_val = (__u32)val;
    bpf_probe_write_kernel((void *)addr, sizeof(new_val), &new_val);
}

// SIE helper 1: memory store -> mem[r14+0xa4] (4B)
static __always_inline void __sie_6_1(struct pt_regs *regs, u64 val) {
    u64 addr = (u64)(regs->r14) + 0xa4;
    __u32 new_val = (__u32)val;
    bpf_probe_write_kernel((void *)addr, sizeof(new_val), &new_val);
}

#define X_TUNE_0(func_name, location_str) \
    static int __xk_policy_6_0(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(__xk_6_0) { \
        struct x_ctx __x_ctx = { .regs = ctx, .set_fn = &__sie_6_0 }; \
        return __xk_policy_6_0(&__x_ctx, ctx); \
    } \
    static int __xk_policy_6_0(struct x_ctx *x_ctx, struct pt_regs *ctx)

#define X_TUNE_1(func_name, location_str) \
    static int __xk_policy_6_1(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(__xk_6_1) { \
        struct x_ctx __x_ctx = { .regs = ctx, .set_fn = &__sie_6_1 }; \
        return __xk_policy_6_1(&__x_ctx, ctx); \
    } \
    static int __xk_policy_6_1(struct x_ctx *x_ctx, struct pt_regs *ctx)

#endif // __MY_POLICY_6_INTERNAL_H__
