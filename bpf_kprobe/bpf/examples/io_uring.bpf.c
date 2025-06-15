// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "util.bpf.h"
#include "kfuncs.bpf.h"

char LICENSE[] SEC("license") = "GPL";

SEC("kprobe/dev_gro_receive+0x210")
int BPF_KPROBE(dev_gro_receive_0x210)
{
    u64 eax = BPF_EAX(ctx);

    #define NEW_CONST 2
    if (eax >= NEW_CONST) {
        BPF_SET_JG_TRUE(ctx);
    } else {
        BPF_SET_JG_FALSE(ctx);
    }

    return 0;
}