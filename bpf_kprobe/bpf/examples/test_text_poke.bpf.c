// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

BPF_ONESHOT_INIT(test_text_poke) {
    bpf_printk("hello world\n");
    return 0;
}

BPF_ONESHOT_EXIT(test_text_poke) {
    bpf_printk("bye world\n");
    return 0;
}