// SPDX-License-Identifier: GPL-2.0
/*
 * kprobe.c — Auxiliary kprobe management for global consistency
 *
 * Manages guard/unguard kprobe pairs at SS entry/exit points.
 * During a transition the kprobes track a global refcount:
 *   - guard  (SS entry): if refcount was already 0, record end time
 *   - unguard (SS exit): decrement; if it hits 0, record end time
 */

#define pr_fmt(fmt) "xkernel: " fmt

#include "kprobe.h"
#include "core.h"

#include <linux/kernel.h>
#include <linux/kprobes.h>
#include <linux/mutex.h>

/* ── State ───────────────────────────────────────────────────────── */

static bool		enabled;
static DEFINE_MUTEX(kprobe_mtx);

/* ── Enable / disable ────────────────────────────────────────────── */

void xk_enable_aux_kprobes(void)	{ WRITE_ONCE(enabled, true); }
void xk_disable_aux_kprobes(void)	{ WRITE_ONCE(enabled, false); }
bool xk_aux_kprobes_enabled(void)	{ return READ_ONCE(enabled); }

/* ── Kprobe handlers ─────────────────────────────────────────────── */

/*
 * Guard handler (SS entry): if inc_not_zero returns 0 the refcount
 * was already 0 → transition is complete, record the timestamp.
 */
static int handler_guard(struct kprobe *kp, struct pt_regs *regs)
{
	if (!xk_aux_kprobes_enabled())
		return 0;

	if (xk_refcount_inc_not_zero() == 0)
		xk_record_end_time();

	return 0;
}

/*
 * Unguard handler (SS exit): decrement refcount.  When it hits 0
 * the last thread has left SS → record the timestamp.
 */
static int handler_unguard(struct kprobe *kp, struct pt_regs *regs)
{
	if (!xk_aux_kprobes_enabled())
		return 0;

	if (xk_refcount_dec_if_positive() == 0)
		xk_record_end_time();

	return 0;
}

/* ── Attach / detach ─────────────────────────────────────────────── */

static void init_kprobe_pair(struct xk_target_func *func, bool forward)
{
	memset(&func->guard_kp, 0, sizeof(func->guard_kp));
	memset(&func->unguard_kp, 0, sizeof(func->unguard_kp));

	func->guard_kp.symbol_name   = func->name;
	func->unguard_kp.symbol_name = func->name;
	func->guard_kp.offset        = func->soff;
	func->unguard_kp.offset      = func->eoff;

	/*
	 * Forward and reverse transitions use the same refcount logic:
	 * guard increments (if non-zero), unguard decrements.
	 */
	(void)forward;  /* reserved for future asymmetric handlers */
	func->guard_kp.pre_handler   = handler_guard;
	func->unguard_kp.pre_handler = handler_unguard;

	func->guard_attached   = false;
	func->unguard_attached = false;
}

int xk_attach_aux_kprobes(bool forward)
{
	struct xk_target_func *func;
	int ret;

	mutex_lock(&kprobe_mtx);
	xk_disable_aux_kprobes();
	xk_refcount_reset();

	list_for_each_entry(func, &xk_target_funcs, list) {
		init_kprobe_pair(func, forward);

		ret = register_kprobe(&func->guard_kp);
		if (ret < 0) {
			pr_warn("skip guard [%s+0x%lx]: %d\n",
				func->name, func->soff, ret);
		} else {
			func->guard_attached = true;
		}

		ret = register_kprobe(&func->unguard_kp);
		if (ret < 0) {
			pr_warn("skip unguard [%s+0x%lx]: %d\n",
				func->name, func->eoff, ret);
		} else {
			func->unguard_attached = true;
		}
	}

	mutex_unlock(&kprobe_mtx);
	return 0;
}

void xk_detach_aux_kprobes(void)
{
	struct xk_target_func *func;

	mutex_lock(&kprobe_mtx);

	list_for_each_entry(func, &xk_target_funcs, list) {
		if (func->guard_attached) {
			unregister_kprobe(&func->guard_kp);
			func->guard_attached = false;
		}
		if (func->unguard_attached) {
			unregister_kprobe(&func->unguard_kp);
			func->unguard_attached = false;
		}
	}

	mutex_unlock(&kprobe_mtx);
}
