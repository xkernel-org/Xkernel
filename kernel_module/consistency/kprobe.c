#include "kprobe.h"
#include "core.h"

#include <linux/bpf.h>
#include <linux/filter.h>
#include <linux/fs.h>
#include <linux/hash.h>
#include <linux/kernel.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>
#include <linux/limits.h>
#include <linux/module.h>
#include <linux/sched.h>
#include <linux/slab.h>
#include <linux/spinlock.h>

bool aux_kprobes_on = false;
static DEFINE_MUTEX(aux_kprobes_mtx);

extern ktime_t start;
extern ktime_t end;

int xk_enable_auxiliary_kprobes(void) {
  WRITE_ONCE(aux_kprobes_on, true);
  return 0;
}

int xk_disable_auxiliary_kprobes(void) {
  WRITE_ONCE(aux_kprobes_on, false);
  return 0;
}

int xk_is_auxiliary_kprobes_on(void) { return READ_ONCE(aux_kprobes_on); }

// Transition phase: old value -> new value
// kprobe: increment the refcount
// static int handler_guard(struct kprobe *kp, struct pt_regs *regs) {
static int handler_guard(struct kprobe *kp, struct pt_regs *regs) {

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
        if (dbg_cnt0++ < 10) {
            pr_info("Incrementing refcount %d for [%d/%s] in guard, %d\n", 
                xk_refcount(), current->pid, task_name, dbg_cnt0);
        }
    } else if (strncmp(task_name, "test 1", 6) == 0) {
        static int dbg_cnt1 = 0;
        if (dbg_cnt1++ < 10) {
            pr_info("Incrementing refcount %d for [%d/%s] in guard, %d\n", 
                xk_refcount(), current->pid, task_name, dbg_cnt1);
        }
    } else if (strncmp(task_name, "test 2", 6) == 0) {
        static int dbg_cnt2 = 0;
        if (dbg_cnt2++ < 10) {
            pr_info("Incrementing refcount %d for [%d/%s] in guard, %d\n", 
                xk_refcount(), current->pid, task_name, dbg_cnt2);
        }
    } else if (strncmp(task_name, "test 3", 6) == 0) {
        static int dbg_cnt3 = 0;
        if (dbg_cnt3++ < 10) {
            pr_info("Incrementing refcount %d for [%d/%s] in guard, %d\n", 
                xk_refcount(), current->pid, task_name, dbg_cnt3);
        }
    }
#endif

  if (xk_inc_not_zero() == 0) {
    xk_enable_ir_kprobes();
    if (end == 0)
      end = ktime_get();
  }

  return 0;
}

// kretprobe: decrement the refcount
static int handler_unguard(struct kprobe *kp, struct pt_regs *regs) {
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
        if (dbg_cnt0++ < 10) {
            pr_info("Decrementing refcount %d for [%d/%s] in unguard, %d\n", 
                xk_refcount(), current->pid, task_name, dbg_cnt0);
        }
    } else if (strncmp(task_name, "test 1", 6) == 0) {
        static int dbg_cnt1 = 0;
        if (dbg_cnt1++ < 10) {
            pr_info("Decrementing refcount %d for [%d/%s] in unguard, %d\n", 
                xk_refcount(), current->pid, task_name, dbg_cnt1);
        }
    } else if (strncmp(task_name, "test 2", 6) == 0) {
        static int dbg_cnt2 = 0;
        if (dbg_cnt2++ < 10) {
            pr_info("Decrementing refcount %d for [%d/%s] in unguard, %d\n", 
                xk_refcount(), current->pid, task_name, dbg_cnt2);
        }
    } else if (strncmp(task_name, "test 3", 6) == 0) {
        static int dbg_cnt3 = 0;
        if (dbg_cnt3++ < 10) {
            pr_info("Decrementing refcount %d for [%d/%s] in unguard, %d\n", 
                xk_refcount(), current->pid, task_name, dbg_cnt3);
        }
    }
#endif

  if (xk_dec_if_positive() == 0) {
    xk_enable_ir_kprobes();
    if (end == 0)
      end = ktime_get();
  }

  return 0;
}

// Transition phase: old value -> new value
// kprobe: increment the refcount
// static int reverse_handler_guard(struct kprobe *kp, struct pt_regs *regs) {
static int reverse_handler_guard(struct kprobe *kp, struct pt_regs *regs) {
  if (!xk_is_auxiliary_kprobes_on())
    return 0;

  if (xk_inc_not_zero() == 0) {
    xk_disable_ir_kprobes();
    if (end == 0)
      end = ktime_get();
  }

  return 0;
}

// kretprobe: decrement the refcount
static int reverse_handler_unguard(struct kprobe *kp, struct pt_regs *regs) {
  if (!xk_is_auxiliary_kprobes_on())
    return 0;

  if (xk_dec_if_positive() == 0) {
    xk_disable_ir_kprobes();
    if (end == 0)
      end = ktime_get();
  }

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
  memset(&func->guard_kp, 0, sizeof(func->guard_kp));
  memset(&func->unguard_kp, 0, sizeof(func->unguard_kp));

  func->guard_kp.symbol_name = func->name;
  func->unguard_kp.symbol_name = func->name;

  func->guard_kp.offset = func->soff;
  func->unguard_kp.offset = func->eoff;

  if (direction) {
    func->guard_kp.pre_handler = handler_guard;
    func->unguard_kp.pre_handler = handler_unguard;
  } else {
    func->guard_kp.pre_handler = reverse_handler_guard;
    func->unguard_kp.pre_handler = reverse_handler_unguard;
  }

  func->attached_guard_kp = false;
  func->attached_unguard_kp = false;
}

int xk_attach_auxiliary_kprobes(bool direction, char *debug_info) {
  struct xk_target_function *func;
  int ret;

  pr_debug("xk_attach_auxiliary_kprobes called by %s\n", debug_info);

  mutex_lock(&aux_kprobes_mtx);

  xk_disable_auxiliary_kprobes();

  xk_reset_refcount();

  list_for_each_entry(func, &xk_target_functions, list) {
    xk_init_aux_kp(func, direction);
    ret = register_kprobe(&func->guard_kp);
    if (ret < 0) {
      pr_err("Failed to register Guard Kprobe for [%s], error: %d\n",
             func->name, ret);
      goto err;
    }
    func->attached_guard_kp = true;
    ret = register_kprobe(&func->unguard_kp);
    if (ret < 0) {
      pr_err("Failed to register Unguard Kprobe for [%s], error: %d\n",
             func->name, ret);
      goto err;
    }
    func->attached_unguard_kp = true;
    pr_debug("Attached Guard/Unguard Kprobes to [%s]\n", func->name);
  }
  mutex_unlock(&aux_kprobes_mtx);
  return 0;
err:
  mutex_unlock(&aux_kprobes_mtx);
  xk_detach_auxiliary_kprobes("xk_attach_auxiliary_kprobes");
  return ret;
}

void xk_detach_auxiliary_kprobes(char *debug_info) {
  struct xk_target_function *func;

  pr_debug("xk_detach_auxiliary_kprobes called by %s\n", debug_info);

  mutex_lock(&aux_kprobes_mtx);

  list_for_each_entry(func, &xk_target_functions, list) {
    if (func->attached_guard_kp) {
      unregister_kprobe(&func->guard_kp);
      func->attached_guard_kp = false;
    }
    if (func->attached_unguard_kp) {
      unregister_kprobe(&func->unguard_kp);
      func->attached_unguard_kp = false;
    }
    pr_debug("Detached Guard/Unguard Kprobes from [%s]\n", func->name);
  }
  mutex_unlock(&aux_kprobes_mtx);
}
