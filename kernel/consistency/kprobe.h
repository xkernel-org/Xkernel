/* SPDX-License-Identifier: GPL-2.0 */
/*
 * kprobe.h — Auxiliary kprobe management for global consistency
 *
 * Guard/unguard kprobes are placed at SS entry/exit points.
 * They track the refcount of threads still inside SS so the
 * daemon knows when the transition is complete.
 */
#ifndef XK_CONSISTENCY_KPROBE_H
#define XK_CONSISTENCY_KPROBE_H

#include <linux/types.h>

int  xk_attach_aux_kprobes(bool forward);
void xk_detach_aux_kprobes(void);

void xk_enable_aux_kprobes(void);
void xk_disable_aux_kprobes(void);
bool xk_aux_kprobes_enabled(void);

#endif /* XK_CONSISTENCY_KPROBE_H */
