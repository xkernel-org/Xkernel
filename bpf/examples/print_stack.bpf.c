// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/__x64_sys_clone")
int kprobe__sys_clone(struct pt_regs *ctx) {

    store_call_stack(ctx);

    return 0;
}