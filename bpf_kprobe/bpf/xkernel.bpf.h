#ifndef __XKERNEL_H__
#define __XKERNEL_H__

#include "kfuncs.bpf.h"
#include "util.bpf.h"

char LICENSE[] SEC("license") = "GPL";

#define BPF_ONESHOT_INIT(name) \
    SEC("syscall") \
    int oneshot_init_##name(void *ctx) \

#define BPF_ONESHOT_EXIT(name) \
    SEC("syscall") \
    int oneshot_exit_##name(void *ctx) \

#endif