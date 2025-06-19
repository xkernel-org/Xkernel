// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "util.bpf.h"
#include "kfuncs.bpf.h"

char LICENSE[] SEC("license") = "GPL";

// The probes are placed too close to each other. As a result, even though
// only *one* of the two load instructions is executed each time, the
// handler after the 1st load is always executed.
//
//   1:   jb 5
//   2:   mov           # the 1st load of interest
//   3:   mov           # patched to jmp
//   4:   jmp elsewhere
//   5:   mov           # the 2nd load of interest
//   6:   jmp 3         # patched to int3
//
bool the_second_load;

SEC("kprobe/ttwu_do_activate+0x17e")
int BPF_KPROBE(ttwu_do_activate_0x17e, struct rq *rq, struct task_struct *p, int wake_flags)
{
    u16 id = bpf_get_smp_processor_id();
    if (id == 42) {
        bpf_printk("\n");
        bpf_printk("ctx->si: %lu (previous avg_idle)", ctx->si);
        the_second_load = false;
    }
    return 0;
}

SEC("kprobe/ttwu_do_activate+0x1b3")
int BPF_KPROBE(ttwu_do_activate_0x1b3, struct rq *rq, struct task_struct *p, int wake_flags)
{
    u16 id = bpf_get_smp_processor_id();
    if (id == 42 && !the_second_load) {
        bpf_printk("ctx->ax: %lu (updated avg_idle)", ctx->ax);
    }
    return 0;
}

SEC("kprobe/ttwu_do_activate+0x1cc")
int BPF_KPROBE(ttwu_do_activate_0x1cc, struct rq *rq, struct task_struct *p, int wake_flags)
{
    u16 id = bpf_get_smp_processor_id();
    if (id == 42) {
        bpf_printk("ctx->cx: %lu (updated avg_idle)", ctx->cx);
        the_second_load = true;
    }
    return 0;
}

//     ffffffff98362720 <.data>:
//     ffffffff98362720:       0f 1f 44 00 00          nopl   0x0(%rax,%rax,1)
//     ...
//     ffffffff983628ae:       48 29 f2                sub    %rsi,%rdx
//     ffffffff983628b1:       48 01 c9                add    %rcx,%rcx
//     ffffffff983628b4:       48 29 c2                sub    %rax,%rdx
//     ffffffff983628b7:       48 8d 42 07             lea    0x7(%rdx),%rax
//     ffffffff983628bb:       48 0f 49 c2             cmovns %rdx,%rax
//     ffffffff983628bf:       48 c1 f8 03             sar    $0x3,%rax
// (*) ffffffff983628c3:       48 01 f0                add    %rsi,%rax
// (*) ffffffff983628c6:       48 39 c1                cmp    %rax,%rcx
//     ffffffff983628c9:       72 19                   jb     0xffffffff983628e4
//     ffffffff983628cb:       49 89 84 24 c8 0b 00    mov    %rax,0xbc8(%r12)

#define XKERNEL_DEBUG

#ifdef XKERNEL_DEBUG
static int counter;
#endif // XKERNEL_DEBUG

SEC("kprobe/ttwu_do_activate+0x1a3")
int BPF_KPROBE(ttwu_do_activate_0x1a3, struct rq *rq, struct task_struct *p, int wake_flags)
{
    u16 id = bpf_get_smp_processor_id();
    if (id == 42) {
        // manipulate diff which is signed 64-bit integer
        s64 rax = BPF_AX(ctx);
        bool is_neg = rax < 0;
        u64 abs_rax = is_neg ? -rax : rax;
        abs_rax *= 2;
        rax = is_neg ? -abs_rax : abs_rax;
        kfuncs_probe_write_kernel(&ctx->ax, sizeof(rax), &rax, sizeof(rax));
        bpf_printk("ctx->ax: %ld (diff)", ctx->ax);
    }
    return 0;
}
