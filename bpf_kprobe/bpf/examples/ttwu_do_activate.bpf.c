// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "util.bpf.h"
#include "kfuncs.bpf.h"

char LICENSE[] SEC("license") = "GPL";

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
#ifdef XKERNEL_DEBUG
    counter++;
    if (counter > 300) {
        bpf_printk("ttwu_do_activate_0x1a3\n");
        dump_ctx(ctx);
#endif // XKERNEL_DEBUG
        // https://elixir.bootlin.com/linux/v6.14.7/source/arch/x86/include/asm/ptrace.h#L103
        u64 rax = ctx->ax;
        // rax >>= 0; // kprobe_no_change
        // rax >>= 4; // kprobe_right_4
        // rax <<= 4; // kprobe_left_4
        // rax <<= 16; // kprobe_left_16
        rax = 0;
        kfuncs_probe_write_kernel(&ctx->ax, sizeof(rax), &rax, sizeof(rax));
#ifdef XKERNEL_DEBUG
        dump_ctx(ctx);
        counter = 0;
    }
#endif // XKERNEL_DEBUG
    return 0;
}
