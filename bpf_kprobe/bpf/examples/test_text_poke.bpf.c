// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("syscall")
int test_text_poke(void *ctx) {
    bpf_printk("hello world\n");
    return 0;
}