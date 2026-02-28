// SPDX-License-Identifier: GPL-2.0
// Auto-generated SIE indirection for test group 2
#ifndef __MY_POLICY_2_INTERNAL_H__
#define __MY_POLICY_2_INTERNAL_H__

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "cs_artifact.bpf.h"

// SIE helper 0: simple -> %esi
static __always_inline void __sie_2_0(struct pt_regs *regs, u64 val) {
    u64 new_val = val;
    sie_write_kernel(&regs->si, sizeof(regs->si), &new_val);
}

#define X_TUNE_0(func_name, location_str) \
    static int __xk_policy_2_0(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(__xk_2_0) { \
        struct x_ctx __x_ctx = { .regs = ctx, .set_fn = &__sie_2_0 }; \
        return __xk_policy_2_0(&__x_ctx, ctx); \
    } \
    static int __xk_policy_2_0(struct x_ctx *x_ctx, struct pt_regs *ctx)

#endif // __MY_POLICY_2_INTERNAL_H__
