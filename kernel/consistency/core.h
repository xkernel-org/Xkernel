/* SPDX-License-Identifier: GPL-2.0 */
/*
 * core.h — Xkernel global consistency module
 *
 * Shared data structures and helpers for the stop_machine-based
 * global transition protocol (Mode 2).
 */
#ifndef XK_CONSISTENCY_CORE_H
#define XK_CONSISTENCY_CORE_H

#include <linux/atomic.h>
#include <linux/kprobes.h>
#include <linux/list.h>
#include <linux/types.h>

/* ── Constants ───────────────────────────────────────────────────── */

#define XK_MAX_FUNC_NAME_LEN	128
#define XK_MAX_STACK_ENTRIES	100

/* ── Transition state machine ────────────────────────────────────── */

enum xk_state {
	XK_STATE_PENDING,
	XK_STATE_DONE,
	XK_STATE_FAILED,
	XK_STATE_REVERSE_PENDING,
	XK_STATE_REVERSE_DONE,
	XK_STATE_REVERSE_FAILED,
};

/* ── Target function (one per SS/CS range) ───────────────────────── */

struct xk_target_func {
	char			name[XK_MAX_FUNC_NAME_LEN];
	unsigned long		addr;		/* resolved symbol address */
	unsigned long		soff;		/* span start offset      */
	unsigned long		eoff;		/* span end offset        */

	struct kprobe		guard_kp;	/* SS entry kprobe  */
	struct kprobe		unguard_kp;	/* SS exit kprobe   */
	bool			guard_attached;
	bool			unguard_attached;

	struct list_head	list;
};

extern struct list_head xk_target_funcs;

/* ── Inline helpers ──────────────────────────────────────────────── */

/**
 * xk_addr_in_span() - Check whether a stack address falls within a span.
 * @stack_addr:  address from the stack trace
 * @func_addr:   resolved base address of the function
 * @soff:        span start offset (relative to func_addr)
 * @eoff:        span end offset   (relative to func_addr)
 */
static inline bool xk_addr_in_span(unsigned long stack_addr,
				    unsigned long func_addr,
				    unsigned long soff,
				    unsigned long eoff)
{
	return stack_addr >= func_addr + soff &&
	       stack_addr <  func_addr + eoff;
}

/* ── Refcount (tracks threads still inside SS) ───────────────────── */

void xk_refcount_reset(void);
int  xk_refcount_read(void);
void xk_refcount_inc(void);
int  xk_refcount_inc_not_zero(void);
void xk_refcount_dec(void);
int  xk_refcount_dec_if_positive(void);

/* ── Transition timing (shared between core.c and kprobe.c) ──────── */

void xk_record_end_time(void);

#endif /* XK_CONSISTENCY_CORE_H */
