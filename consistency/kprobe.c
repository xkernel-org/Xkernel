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
static DEFINE_MUTEX(aux_kprobes_mtx);

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

// Transition phase: old value -> new value
// kprobe: increment the refcount
// static int handler_guard(struct kprobe *kp, struct pt_regs *regs) {
static int handler_guard(struct kretprobe_instance *ri, struct pt_regs *regs) {

    if (!xk_is_auxiliary_kprobes_on())
        return 0;

    #if 0

    char task_name[128];
    char *pos = strchr(current->comm, '/');
    if (pos) {
        *pos = '\0';
    }
    strncpy(task_name, current->comm, sizeof(task_name));
    task_name[sizeof(task_name) - 1] = '\0';
    if (strncmp(task_name, "test 0", 6) == 0) {
        static int dbg_cnt0 = 0;
        if (dbg_cnt0++ < 100000) {
            pr_info("Incrementing refcount %d for [%d/%s] in guard\n", 
                xk_refcount(), current->pid, task_name);
        }
    } else if (strncmp(task_name, "test 1", 6) == 0) {
        static int dbg_cnt1 = 0;
        if (dbg_cnt1++ < 100000) {
            pr_info("Incrementing refcount %d for [%d/%s] in guard\n", 
                xk_refcount(), current->pid, task_name);
        }
    } else if (strncmp(task_name, "test 2", 6) == 0) {
        static int dbg_cnt2 = 0;
        if (dbg_cnt2++ < 100000) {
            pr_info("Incrementing refcount %d for [%d/%s] in guard\n", 
                xk_refcount(), current->pid, task_name);
        }
    } else if (strncmp(task_name, "test 3", 6) == 0) {
        static int dbg_cnt3 = 0;
        if (dbg_cnt3++ < 100000) {
            pr_info("Incrementing refcount %d for [%d/%s] in guard\n", 
                xk_refcount(), current->pid, task_name);
        }
    }
    #endif

    if (xk_inc_not_zero() == 0)
        xk_enable_ir_kprobes();
    
    return 0;
}

// kretprobe: decrement the refcount
static int handler_unguard(struct kretprobe_instance *ri, struct pt_regs *regs) {
    if (!xk_is_auxiliary_kprobes_on())
        return 0;

    #if 0
    char task_name[128];
    char *pos = strchr(current->comm, '/');
    if (pos) {
        *pos = '\0';
    }
    strncpy(task_name, current->comm, sizeof(task_name));
    task_name[sizeof(task_name) - 1] = '\0';
    if (strncmp(task_name, "test 0", 6) == 0) {
        static int dbg_cnt0 = 0;
        if (dbg_cnt0++ < 100000) {
            pr_info("Decrementing refcount %d for [%d/%s] in unguard\n", 
                xk_refcount(), current->pid, task_name);
        }
    } else if (strncmp(task_name, "test 1", 6) == 0) {
        static int dbg_cnt1 = 0;
        if (dbg_cnt1++ < 100000) {
            pr_info("Decrementing refcount %d for [%d/%s] in unguard\n", 
                xk_refcount(), current->pid, task_name);
        }
    } else if (strncmp(task_name, "test 2", 6) == 0) {
        static int dbg_cnt2 = 0;
        if (dbg_cnt2++ < 100000) {
            pr_info("Decrementing refcount %d for [%d/%s] in unguard\n", 
                xk_refcount(), current->pid, task_name);
        }
    } else if (strncmp(task_name, "test 3", 6) == 0) {
        static int dbg_cnt3 = 0;
        if (dbg_cnt3++ < 100000) {
            pr_info("Decrementing refcount %d for [%d/%s] in unguard\n", 
                xk_refcount(), current->pid, task_name);
        }
    }
    #endif

    if (xk_dec_if_positive() == 0)
        xk_enable_ir_kprobes();

    return 0;
}

// Transition phase: old value -> new value
// kprobe: increment the refcount
// static int reverse_handler_guard(struct kprobe *kp, struct pt_regs *regs) {
static int reverse_handler_guard(struct kretprobe_instance *ri, struct pt_regs *regs) {
    if (!xk_is_auxiliary_kprobes_on())
        return 0;

    if (xk_inc_not_zero() == 0)
        xk_disable_ir_kprobes();

    return 0;
}

// kretprobe: decrement the refcount
static int reverse_handler_unguard(struct kretprobe_instance *ri, struct pt_regs *regs) {
    if (!xk_is_auxiliary_kprobes_on())
        return 0;

    if (xk_dec_if_positive() == 0)
        xk_disable_ir_kprobes();

    return 0;
}

/**
 * Initialize the guard kprobe for a target function.
 * @param func: The target function.
 * @param direction: The direction of the transition.
 *                      true: enable_ir_kprobes
 *                      false: disable_ir_kprobes
 */
static void xk_init_aux_kp(struct xk_target_function *func, bool direction) {
    memset(&func->aux_kp, 0, sizeof(func->aux_kp));
    
    func->aux_kp.kp.symbol_name = func->name;

    func->aux_kp.data_size = sizeof(int);

    if (direction) {
        func->aux_kp.entry_handler = handler_guard;
        func->aux_kp.handler = handler_unguard;
    } else {
        func->aux_kp.entry_handler = reverse_handler_guard;
        func->aux_kp.handler = reverse_handler_unguard;
    }

    func->attached_aux_kp = false;
}

int xk_attach_auxiliary_kprobes(bool direction, char *debug_info) {
    struct xk_target_function *func;
    int ret;

    pr_info("xk_attach_auxiliary_kprobes called by %s\n", debug_info);

    mutex_lock(&aux_kprobes_mtx);

    xk_disable_auxiliary_kprobes();

    xk_reset_refcount();
    
    list_for_each_entry(func, &xk_target_functions, list) {
        xk_init_aux_kp(func, direction);
        ret = register_kretprobe(&func->aux_kp);
        if (ret < 0) {
            pr_err("Failed to register Unguard Kretprobe for [%s], error: %d\n", func->name, ret);
            unregister_kretprobe(&func->aux_kp);
            mutex_unlock(&aux_kprobes_mtx);
            return ret;
        }
        func->attached_aux_kp = true;
        pr_info("Attached Guard/Unguard Kprobes to [%s]\n", func->name);
    }
    mutex_unlock(&aux_kprobes_mtx);
    return 0;
}

void xk_detach_auxiliary_kprobes(char *debug_info) {
    struct xk_target_function *func;

    pr_info("xk_detach_auxiliary_kprobes called by %s\n", debug_info);

    mutex_lock(&aux_kprobes_mtx);
    
    list_for_each_entry(func, &xk_target_functions, list) {
        if (func->attached_aux_kp) {
            unregister_kretprobe(&func->aux_kp);
            func->attached_aux_kp = false;
        }
        pr_info("Detached Guard/Unguard Kprobes from [%s]\n", func->name);
    }
    mutex_unlock(&aux_kprobes_mtx);
}

