#include "kprobe.h"
#include "core.h"

#include <linux/kernel.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>
#include <linux/module.h>
#include <linux/mutex.h>

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

// Forward transition: guard at SS entry increments refcount.
// When xk_inc_not_zero() returns 0, refcount was already 0 — transition done.
static int handler_guard(struct kprobe *kp, struct pt_regs *regs) {
  if (!xk_is_auxiliary_kprobes_on())
    return 0;

  if (xk_inc_not_zero() == 0) {
    if (end == 0)
      end = ktime_get();
  }

  return 0;
}

// Forward transition: unguard at SS exit decrements refcount.
// When xk_dec_if_positive() returns 0, last thread left SS — transition done.
static int handler_unguard(struct kprobe *kp, struct pt_regs *regs) {
  if (!xk_is_auxiliary_kprobes_on())
    return 0;

  if (xk_dec_if_positive() == 0) {
    if (end == 0)
      end = ktime_get();
  }

  return 0;
}

// Reverse transition: same refcount logic, used during module unload.
static int reverse_handler_guard(struct kprobe *kp, struct pt_regs *regs) {
  if (!xk_is_auxiliary_kprobes_on())
    return 0;

  if (xk_inc_not_zero() == 0) {
    if (end == 0)
      end = ktime_get();
  }

  return 0;
}

static int reverse_handler_unguard(struct kprobe *kp, struct pt_regs *regs) {
  if (!xk_is_auxiliary_kprobes_on())
    return 0;

  if (xk_dec_if_positive() == 0) {
    if (end == 0)
      end = ktime_get();
  }

  return 0;
}

/**
 * Initialize the guard/unguard kprobe pair for a target function.
 * @param func: The target function.
 * @param direction: true = forward transition, false = reverse transition.
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
      pr_warn("Skipping Guard Kprobe for [%s+0x%lx], error: %d "
              "(offset may not be at instruction boundary)\n",
              func->name, func->soff, ret);
      /* Continue without this guard — stop_machine stack check
       * still covers this span via address range comparison. */
    } else {
      func->attached_guard_kp = true;
    }
    ret = register_kprobe(&func->unguard_kp);
    if (ret < 0) {
      pr_warn("Skipping Unguard Kprobe for [%s+0x%lx], error: %d "
              "(offset may not be at instruction boundary)\n",
              func->name, func->eoff, ret);
    } else {
      func->attached_unguard_kp = true;
    }
    if (func->attached_guard_kp || func->attached_unguard_kp)
      pr_debug("Attached Guard/Unguard Kprobes to [%s]\n", func->name);
  }
  mutex_unlock(&aux_kprobes_mtx);
  return 0;
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
