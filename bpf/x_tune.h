/* x_tune.h — KernelX Programmable Policy API (§3.6)
 *
 * This header provides the user-facing API for writing X-tune policies.
 * Users implement tuning logic using X_TUNE() and call x_set() to update
 * perf-const values. The x-gen tool generates a stub that #includes this
 * header and provides the SIE indirection implementation.
 *
 * Usage:
 *   1. Run: ./xkernel-tool gen <ConstID> -o my_policy.bpf.c
 *   2. Edit my_policy.bpf.c: implement your policy in the X_TUNE block
 *   3. Build: make -C bpf/
 *   4. Load: sudo ./xkernel-tool load <mode> <ConstID>
 *
 * See examples/policy/ for sample X-tune programs.
 */

#ifndef __X_TUNE_H__
#define __X_TUNE_H__

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#include "kfuncs.bpf.h"
#include "xkernel.bpf.h"

/* ── X-tune context ────────────────────────────────────────────────────── */

/* x_ctx is defined in xkernel.bpf.h; typedef the pointer for convenience. */
typedef struct x_ctx *x_handle_t;

/* ── Core APIs ─────────────────────────────────────────────────────────── */

/* x_set — Update the perf-const to a new value (handle version).
 *
 * Invokes the SIE indirection: computes the new architectural state from the
 * symbolic expression and writes it back via pt_regs or kernel memory.
 *
 * @x_ctx: Handle from X_TUNE's first argument.
 * @val:   New source-level value V' of the perf-const.
 * Returns: 0 on success, negative on error.
 */
static __always_inline long x_tune_set(x_handle_t x_ctx, __u64 val) {
    if (!x_ctx || !x_ctx->set_fn)
        return -1;
    x_ctx->set_fn(x_ctx->regs, val);
    return 0;
}

/* x_transition_done is defined in xkernel.bpf.h.
 * Policy code MUST call x_transition_done(x_ctx) before x_set()
 * to ensure the transition safety invariant. */

/* ── X_TUNE macro ──────────────────────────────────────────────────────── */

/* X_TUNE — Define a tuning policy for a perf-const.
 *
 * The macro generates the boilerplate BPF_KPROBE handler. The user implements
 * the body with policy logic. The generated stub provides:
 *   - x_ctx: handle with access to pt_regs and SIE indirection
 *   - ctx: raw pt_regs pointer for reading kernel parameters
 *
 * Example:
 *   X_TUNE(my_policy, tcp_cubic_hystart_check, 0x4F) {
 *       if (!x_transition_done(x_ctx)) return 0;
 *       struct sock *sk = (struct sock *)PT_REGS_PARM1(ctx);
 *       // ... policy logic ...
 *       x_set(x_ctx, new_value);
 *       return 0;
 *   }
 *
 * @name: Unique policy name (becomes the BPF program name).
 * @func: Target kernel function for the kprobe.
 * @offset: Hex offset within the function (probe attachment point).
 */
#define X_TUNE(name, func, offset)                                             \
    static __always_inline void __impl_sie_##name(                             \
        struct pt_regs *regs, __u64 val);                                      \
    static __always_inline int __user_policy_##name(                           \
        x_handle_t x_ctx, struct pt_regs *ctx);                               \
    SEC("kprobe/" #func "+0x" #offset)                                         \
    int BPF_KPROBE(xtune_##name) {                                             \
        struct x_ctx _x_ctx = {                                                \
            .regs = ctx,                                                       \
            .set_fn = __impl_sie_##name,                                       \
        };                                                                     \
        return __user_policy_##name(&_x_ctx, ctx);                             \
    }                                                                          \
    static __always_inline int __user_policy_##name(                           \
        x_handle_t x_ctx, struct pt_regs *ctx)

/* ── Convenience helpers ───────────────────────────────────────────────── */

/* Read a kernel struct field safely (via CO-RE). */
#define X_READ(src, field) BPF_CORE_READ(src, field)

/* Get the Nth function parameter from pt_regs. */
#define X_PARAM(ctx, n) PT_REGS_PARM##n(ctx)

/* Get current PID/TGID. */
static __always_inline __u64 x_get_pid_tgid(void) {
    return bpf_get_current_pid_tgid();
}

/* Get current CPU ID. */
static __always_inline __u32 x_get_cpu(void) {
    return bpf_get_smp_processor_id();
}

#endif /* __X_TUNE_H__ */
