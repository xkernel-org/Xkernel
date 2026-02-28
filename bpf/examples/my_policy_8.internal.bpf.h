// SPDX-License-Identifier: GPL-2.0
// Auto-generated SIE indirection for test group 8
#ifndef __MY_POLICY_8_INTERNAL_H__
#define __MY_POLICY_8_INTERNAL_H__

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "cs_artifact.bpf.h"

// SIE helper 0: cmp_immediate -> FLAGS (cmp new_IV, %eax)
static __always_inline void __sie_8_0(struct pt_regs *regs, u64 val) {
    u32 reg_val = (u32)(regs->ax);
    u32 new_imm = (u32)(val + -1);
    xk_cmp_set_flags32(regs, reg_val, new_imm);
}

#define X_TUNE_0(func_name, location_str) \
    static int __xk_policy_8_0(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(__xk_8_0) { \
        struct x_ctx __x_ctx = { .regs = ctx, .set_fn = &__sie_8_0 }; \
        return __xk_policy_8_0(&__x_ctx, ctx); \
    } \
    static int __xk_policy_8_0(struct x_ctx *x_ctx, struct pt_regs *ctx)

#endif // __MY_POLICY_8_INTERNAL_H__
