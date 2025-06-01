// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "util.bpf.h"
#include "kfuncs.bpf.h"

char LICENSE[] SEC("license") = "GPL";

// 40ms RTT
// SEC("kprobe/hystart_update+0xcc")
// int BPF_KPROBE(hystart_update_0xcc)
// {
//     u64 eax = (u64)(ctx->ax) & 0xffffffff;
//     eax <<= 4;
//     kfuncs_probe_write_kernel(&ctx->ax, sizeof(eax), &eax, sizeof(eax));

//     return 0;
// }

// SEC("kprobe/hystart_update+0xd9")
// int BPF_KPROBE(hystart_update_0xd9)
// {
//     u64 ecx = (u64)(ctx->cx) & 0xffffffff;
//     ecx <<= 1;
//     kfuncs_probe_write_kernel(&ctx->cx, sizeof(ecx), &ecx, sizeof(ecx));

//     return 0;
// }

// 80ms RTT
SEC("kprobe/hystart_update+0xcc")
int BPF_KPROBE(hystart_update_0xcc)
{
    u64 eax = (u64)(ctx->ax) & 0xffffffff;
    eax <<= 3;
    kfuncs_probe_write_kernel(&ctx->ax, sizeof(eax), &eax, sizeof(eax));

    return 0;
}

SEC("kprobe/hystart_update+0xd9")
int BPF_KPROBE(hystart_update_0xd9)
{
    u64 ecx = (u64)(ctx->cx) & 0xffffffff;
    ecx <<= 1;
    kfuncs_probe_write_kernel(&ctx->cx, sizeof(ecx), &ecx, sizeof(ecx));

    return 0;
}