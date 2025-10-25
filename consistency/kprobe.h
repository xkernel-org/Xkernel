#ifndef XK_KPROBE_H
#define XK_KPROBE_H

#include "core.h"

int xk_refcount(void);
void xk_inc_refcount(void);
void xk_inc_if_not_zero(void);
void xk_dec_refcount(void);
void xk_dec_if_positive(void);

void xk_enable_ir_kprobes(void);
void xk_disable_ir_kprobes(void);
int xk_attach_auxiliary_kprobes(void);
void xk_detach_auxiliary_kprobes(void);

void xk_init_guard_kp(struct xk_target_function *func);

#endif