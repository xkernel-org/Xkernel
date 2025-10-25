#include "kprobe.h"

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>
#include <linux/limits.h>

// Global refcount
atomic_t xk_global_refcount = ATOMIC_INIT(0);

int xk_refcount(void) {
    return atomic_read(&xk_global_refcount);
}

void xk_inc_refcount(void) {
    atomic_inc(&xk_global_refcount);
}

void xk_inc_if_not_zero(void) {
    atomic_inc_not_zero(&xk_global_refcount);
}

void xk_dec_refcount(void) {
    atomic_dec(&xk_global_refcount);
}

void xk_dec_if_positive(void) {
    atomic_dec_if_positive(&xk_global_refcount);
}

static int handler_guard(struct kprobe *kp, struct pt_regs *regs) {
    xk_inc_if_not_zero();
    return 0;
}

static void handler_unguard(struct kprobe *kp, struct pt_regs *regs, unsigned long flags) {
    xk_dec_if_positive();
}

void xk_enable_ir_kprobes(void) {
}

void xk_disable_ir_kprobes(void) {
}

int xk_attach_auxiliary_kprobes(void) {
    struct xk_target_function *func;
    int ret;
    list_for_each_entry(func, &xk_target_functions, list) {
        ret = register_kprobe(&func->guard_kp);
        if (ret < 0) {
            pr_err("Failed to register Guard Kprobe for function %s\n", func->name);
            return ret;
        }
        func->attached_guard_kp = true;
        pr_info("Attached Guard/Unguard Kprobes to function %s\n", func->name);
    }
    return 0;
}

void xk_detach_auxiliary_kprobes(void) {
    struct xk_target_function *func;
    list_for_each_entry(func, &xk_target_functions, list) {
        if (!func->attached_guard_kp) continue;
        unregister_kprobe(&func->guard_kp);
        func->attached_guard_kp = false;
        pr_info("Detached Guard/Unguard Kprobes from function %s\n", func->name);
    }
}

void xk_init_guard_kp(struct xk_target_function *func) {
    func->guard_kp.symbol_name = func->name;
    func->guard_kp.offset = 0;
    func->guard_kp.pre_handler = handler_guard;
    func->guard_kp.post_handler = handler_unguard;
    func->attached_guard_kp = false;
}

