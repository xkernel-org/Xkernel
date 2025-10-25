#ifndef XK_KPROBE_H
#define XK_KPROBE_H

#include "core.h"

#define TRANSITION_MAP_PATH "/sys/fs/bpf/xkernel/transition_map"

int xk_refcount(void);
void xk_inc_refcount(void);
int xk_inc_if_not_zero(void);
void xk_dec_refcount(void);
int xk_dec_if_positive(void);

int xk_attach_auxiliary_kprobes(bool direction);
void xk_detach_auxiliary_kprobes(void);

#endif