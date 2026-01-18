// Generated BPF kprobe header for test group 1
// Function: cubictcp_acked
// Offset: 0x22A (changed instruction at 0x227, kprobe attach at offset 0x22a)
// Linear relationship: IV = V
// Target register: %eax (base: %rax)

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// 1. Helper: SIE Indirection
static __always_inline void impl_sie_logic_cs1(
    struct pt_regs *regs, u64 val) {
    // Recovered symbolic state expression
    // eax = val
    u64 new_ax = val;
    
    // Writing back to pt_regs using the kfunc
    sie_write_kernel(&regs->ax, sizeof(regs->ax), &new_ax);
}

// 2. X_TUNE macro: wraps BPF_KPROBE and calls user policy
// Usage: X_TUNE(function_name, "file_path:L<line>:<col>:0x<offset>") { ... }
// The macro expands to:
//   - A forward declaration of __user_policy_<func_name>
//   - A BPF_KPROBE function that sets up x_ctx and calls __user_policy_<func_name>
//   - The actual __user_policy_<func_name> function definition (user provides body)
#define X_TUNE(func_name, location_str) \
    static int __user_policy_##func_name(struct x_ctx *x_ctx, struct pt_regs *ctx); \
    SEC("kprobe/" #func_name location_str) \
    int BPF_KPROBE(impl_cs_1) { \
        struct x_ctx x_ctx_local = { \
            .regs = ctx, \
            .set_fn = &impl_sie_logic_cs1, \
        }; \
        return __user_policy_##func_name(&x_ctx_local, ctx); \
    } \
    static int __user_policy_##func_name(struct x_ctx *x_ctx, struct pt_regs *ctx)
