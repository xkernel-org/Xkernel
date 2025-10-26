#include "kprobe.h"

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>
#include <linux/limits.h>
#include <linux/bpf.h>
#include <linux/fs.h>
#include <linux/filter.h>

// Global refcount
atomic_t xk_global_refcount = ATOMIC_INIT(0);

bool aux_kprobes_on = false;

int xk_enable_auxiliary_kprobes(void) {
    WRITE_ONCE(aux_kprobes_on, true);
    return 0;
}

int xk_disable_auxiliary_kprobes(void) {
    WRITE_ONCE(aux_kprobes_on, false);
    return 0;
}

int xk_is_auxiliary_kprobes_on(void) {
    return READ_ONCE(aux_kprobes_on);
}

int xk_refcount(void) {
    return atomic_read(&xk_global_refcount);
}

void xk_inc_refcount(void) {
    atomic_inc(&xk_global_refcount);
}

int xk_inc_not_zero(void) {
   return atomic_inc_not_zero(&xk_global_refcount);
}

void xk_dec_refcount(void) {
    atomic_dec(&xk_global_refcount);
}

int xk_dec_if_positive(void) {
    return atomic_dec_if_positive(&xk_global_refcount);
}

void xk_reset_refcount(void) {
    atomic_set(&xk_global_refcount, 0);
}

static int handler_guard(struct kprobe *kp, struct pt_regs *regs) {
    if (!xk_is_auxiliary_kprobes_on()) {
        return 0;
    }

    if (xk_inc_not_zero() == 0) {
        xk_enable_ir_kprobes();
    }
    return 0;
}

static int reverse_handler_guard(struct kprobe *kp, struct pt_regs *regs) {
    
    if (!xk_is_auxiliary_kprobes_on()) {
        return 0;
    }

    if (xk_inc_not_zero() == 0) {
        xk_disable_ir_kprobes();
    }
    return 0;
}

static void handler_unguard(struct kprobe *kp, struct pt_regs *regs, unsigned long flags) {
    
    if (!xk_is_auxiliary_kprobes_on()) {
        return;
    }
    
    if (xk_dec_if_positive() == 0) {
        xk_enable_ir_kprobes();
    }
}

static void reverse_handler_unguard(struct kprobe *kp, struct pt_regs *regs, unsigned long flags) {
    
    if (!xk_is_auxiliary_kprobes_on()) {
        return;
    }

    if (xk_dec_if_positive() == 0) {
        xk_disable_ir_kprobes();
    }
}

/**
 * Initialize the guard kprobe for a target function.
 * @param func: The target function.
 * @param direction: The direction of the transition.
 *                      true: enable_ir_kprobes
 *                      false: disable_ir_kprobes
 */
static void xk_init_guard_kp(struct xk_target_function *func, bool direction) {
    memset(&func->guard_kp, 0, sizeof(func->guard_kp));
    func->guard_kp.symbol_name = func->name;
    if (direction) {
        func->guard_kp.pre_handler = handler_guard;
        func->guard_kp.post_handler = handler_unguard;
    } else {
        func->guard_kp.pre_handler = reverse_handler_guard;
        func->guard_kp.post_handler = reverse_handler_unguard;
    }
    func->attached_guard_kp = false;
}

int xk_attach_auxiliary_kprobes(bool direction) {
    struct xk_target_function *func;
    int ret;

    BUG_ON(xk_is_auxiliary_kprobes_on());

    xk_reset_refcount();
    
    list_for_each_entry(func, &xk_target_functions, list) {
        xk_init_guard_kp(func, direction);
        ret = register_kprobe(&func->guard_kp);
        if (ret < 0) {
            pr_err("Failed to register Guard Kprobe for [%s], error: %d\n", func->name, ret);
            return ret;
        }
        func->attached_guard_kp = true;
        pr_info("Attached Guard/Unguard Kprobes to [%s]\n", func->name);
    }
    return 0;
}

void xk_detach_auxiliary_kprobes(void) {
    struct xk_target_function *func;

    BUG_ON(xk_is_auxiliary_kprobes_on());
    
    list_for_each_entry(func, &xk_target_functions, list) {
        if (!func->attached_guard_kp) continue;
        unregister_kprobe(&func->guard_kp);
        func->attached_guard_kp = false;
        pr_info("Detached Guard/Unguard Kprobes from [%s]\n", func->name);
    }
}

