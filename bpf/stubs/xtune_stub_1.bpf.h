// SPDX-License-Identifier: GPL-2.0
// BPF stub for ConstID 1 - BLK_MAX_REQUEST_COUNT
// Hooks: blk_start_plug_nr_ios+0x25 (mov $0x20,%edx)
// Target register: %edx
#ifndef __XTUNE_STUB_1_H__
#define __XTUNE_STUB_1_H__

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "cs_artifact.bpf.h"

// SIE helper 0: simple -> %edx
static __always_inline void __sie_1_0(struct pt_regs *regs, u64 val) {
    u64 new_val = val;
    sie_write_kernel(&regs->dx, sizeof(regs->dx), &new_val);
}

#define X_TUNE_0(func_name, location_str) \
    static int __xk_policy_1_0(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(__xk_1_0) { \
        struct x_ctx __x_ctx = { .regs = ctx, .set_fn = &__sie_1_0 }; \
        return __xk_policy_1_0(&__x_ctx, ctx); \
    } \
    static int __xk_policy_1_0(struct x_ctx *x_ctx, struct pt_regs *ctx)

#endif
