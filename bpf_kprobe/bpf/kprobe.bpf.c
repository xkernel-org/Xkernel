// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "util.bpf.h"
#include "kfuncs.bpf.h"

char LICENSE[] SEC("license") = "GPL";

// struct {
//     __uint(type, BPF_MAP_TYPE_HASH);
//     __type(key, u64);
//     __type(value, u32);
//     __uint(max_entries, 1024);
// } sock_option_map SEC(".maps");

// SEC(".bss")
// static u64 current_sock = 0;
// static u64 cnt = 0;

// static __always_inline bool run_xkernel()
// {
//     u32 *enable = bpf_map_lookup_elem(&sock_option_map, &current_sock);
//     if (!enable) return false;

//     if (*enable) return true;
//     else return false;
// }

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
// SEC("kprobe/hystart_update+0xcc")
// int BPF_KPROBE(hystart_update_0xcc)
// {
//     if (!run_xkernel()) return 0;
    
//     u64 eax = (u64)(ctx->ax) & 0xffffffff;
//     eax <<= 3;
//     kfuncs_probe_write_kernel(&ctx->ax, sizeof(eax), &eax, sizeof(eax));

//     return 0;
// }

// SEC("kprobe/hystart_update+0xd9")
// int BPF_KPROBE(hystart_update_0xd9)
// {
//     if (!run_xkernel()) return 0;
    
//     u64 ecx = (u64)(ctx->cx) & 0xffffffff;
//     ecx <<= 1;
//     kfuncs_probe_write_kernel(&ctx->cx, sizeof(ecx), &ecx, sizeof(ecx));

//     return 0;
// }

// SEC("kprobe/hystart_update")
// int BPF_KPROBE(hystart_update, struct sock *sk, u32 delay)
// {
//     // Record current sock
//     current_sock = (u64)sk;
    
//     u32 *v = bpf_map_lookup_elem(&sock_option_map, &current_sock);
//     if (!v) {
//         u32 enable = ++cnt & 1;
//         bpf_map_update_elem(&sock_option_map, &current_sock, &enable, BPF_ANY);
//     }

//     return 0;
// }

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, u32);
    __type(value, u64);
} per_cpu_gro_list_count_map SEC(".maps");

SEC("kprobe/dev_gro_receive+0x210")
int BPF_KPROBE(dev_gro_receive_0x210)
{
    u32 key = 0;
    u64 *v = bpf_map_lookup_elem(&per_cpu_gro_list_count_map, &key);
    if (!v) return 0;
    
    if (*v == 0) return 0;

    u64 eax = *v;

    kfuncs_probe_write_kernel(&ctx->ax, sizeof(eax), &eax, sizeof(eax));
    // LOG_AX_DEC(ctx);

    *v = 0;

    return 0;
}

SEC("kprobe/dev_gro_receive+0x20d")
int BPF_KPROBE(dev_gro_receive_0x20d)
{
    u64 eax = (u64)(ctx->ax) & 0xffffffff;

    if (eax == 0) return 0;

    #define OLD_CONST 8
    #define NEW_CONST 2

    if (eax < NEW_CONST) return 0;
    
    // LOG_AX_DEC(ctx);

    u64 old_const = OLD_CONST - 1;
    u64 new_const = NEW_CONST - 1;

    u32 key = 0;
    int ret = bpf_map_update_elem(&per_cpu_gro_list_count_map, &key, &eax, BPF_ANY);
    if (ret) return 0;
    
    eax = calc_value(old_const, new_const, eax);

    kfuncs_probe_write_kernel(&ctx->ax, sizeof(eax), &eax, sizeof(eax));

    // LOG_AX_DEC(ctx);

    return 0;
}