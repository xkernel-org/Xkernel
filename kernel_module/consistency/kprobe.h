#ifndef XK_KPROBE_H
#define XK_KPROBE_H

#include "core.h"

#define TRANSITION_MAP_PATH "/sys/fs/bpf/xkernel/transition_map"

int xk_attach_auxiliary_kprobes(bool direction, char *debug_info);
void xk_detach_auxiliary_kprobes(char *debug_info);

int xk_enable_auxiliary_kprobes(void);
int xk_disable_auxiliary_kprobes(void);
int xk_is_auxiliary_kprobes_on(void);

#endif