// SPDX-License-Identifier: GPL-2.0
// Auto-generated SIE indirection for test group 3
#ifndef __MY_POLICY_3_INTERNAL_H__
#define __MY_POLICY_3_INTERNAL_H__

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// SIE helper 0: simple -> %ecx
static __always_inline void __sie_3_0(struct pt_regs *regs, u64 val) {
    u64 new_val = val;
    sie_write_kernel(&regs->cx, sizeof(regs->cx), &new_val);
}

// SIE helper 1: simple -> %eax
static __always_inline void __sie_3_1(struct pt_regs *regs, u64 val) {
    u64 new_val = val;
    sie_write_kernel(&regs->ax, sizeof(regs->ax), &new_val);
}

// SIE helper 2: simple -> %eax
static __always_inline void __sie_3_2(struct pt_regs *regs, u64 val) {
    u64 new_val = val;
    sie_write_kernel(&regs->ax, sizeof(regs->ax), &new_val);
}

// SIE helper 3: simple -> %ecx
static __always_inline void __sie_3_3(struct pt_regs *regs, u64 val) {
    u64 new_val = val;
    sie_write_kernel(&regs->cx, sizeof(regs->cx), &new_val);
}

#define X_TUNE_0(func_name, location_str) \
    static int __xk_policy_3_0(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(__xk_3_0) { \
        struct x_ctx __x_ctx = { .regs = ctx, .set_fn = &__sie_3_0 }; \
        return __xk_policy_3_0(&__x_ctx, ctx); \
    } \
    static int __xk_policy_3_0(struct x_ctx *x_ctx, struct pt_regs *ctx)

#define X_TUNE_1(func_name, location_str) \
    static int __xk_policy_3_1(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(__xk_3_1) { \
        struct x_ctx __x_ctx = { .regs = ctx, .set_fn = &__sie_3_1 }; \
        return __xk_policy_3_1(&__x_ctx, ctx); \
    } \
    static int __xk_policy_3_1(struct x_ctx *x_ctx, struct pt_regs *ctx)

#define X_TUNE_2(func_name, location_str) \
    static int __xk_policy_3_2(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(__xk_3_2) { \
        struct x_ctx __x_ctx = { .regs = ctx, .set_fn = &__sie_3_2 }; \
        return __xk_policy_3_2(&__x_ctx, ctx); \
    } \
    static int __xk_policy_3_2(struct x_ctx *x_ctx, struct pt_regs *ctx)

#define X_TUNE_3(func_name, location_str) \
    static int __xk_policy_3_3(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(__xk_3_3) { \
        struct x_ctx __x_ctx = { .regs = ctx, .set_fn = &__sie_3_3 }; \
        return __xk_policy_3_3(&__x_ctx, ctx); \
    } \
    static int __xk_policy_3_3(struct x_ctx *x_ctx, struct pt_regs *ctx)

#endif // __MY_POLICY_3_INTERNAL_H__
