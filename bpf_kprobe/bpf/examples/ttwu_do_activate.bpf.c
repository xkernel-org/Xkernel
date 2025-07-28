// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "util.bpf.h"
#include "kfuncs.bpf.h"
#include "xkernel.bpf.h"

#define CPU_IDX 24

/*
 * Monitoring where avg_idle gets updated
 */

// 6.14.0-22-generic KASLR
//
// ffffffff92c5c430 <.data>:
// ...
// ffffffff92c5c5bf:	e9 2d ff ff ff       	jmp    0xffffffff92c5c4f1
// ffffffff92c5c5c4:	83 bb 40 0c 00 00 01 	cmpl   $0x1,0xc40(%rbx)
// ffffffff92c5c5cb:	0f 86 b7 00 00 00    	jbe    0xffffffff92c5c688
// ffffffff92c5c5d1:	48 8b b3 c8 0d 00 00 	mov    0xdc8(%rbx),%rsi    // (1)
// ffffffff92c5c5d8:	48 8b 93 48 0c 00 00 	mov    0xc48(%rbx),%rdx    // 0x1a8
// ffffffff92c5c5df:	48 8b 8b d0 0d 00 00 	mov    0xdd0(%rbx),%rcx
// ffffffff92c5c5e6:	48 29 f2             	sub    %rsi,%rdx
// ffffffff92c5c5e9:	48 01 c9             	add    %rcx,%rcx
// ffffffff92c5c5ec:	48 29 c2             	sub    %rax,%rdx
// ffffffff92c5c5ef:	48 8d 42 07          	lea    0x7(%rdx),%rax
// ffffffff92c5c5f3:	48 0f 49 c2          	cmovns %rdx,%rax
// ffffffff92c5c5f7:	48 c1 f8 03          	sar    $0x3,%rax           // (4)
// ffffffff92c5c5fb:	48 01 f0             	add    %rsi,%rax           // 0x1cb
// ffffffff92c5c5fe:	48 39 c1             	cmp    %rax,%rcx
// ffffffff92c5c601:	72 2f                	jb     0xffffffff92c5c632
// ffffffff92c5c603:	48 89 83 c8 0d 00 00 	mov    %rax,0xdc8(%rbx)    // (2)
// ffffffff92c5c60a:	48 c7 83 c0 0d 00 00 	movq   $0x0,0xdc0(%rbx)    // 0x1da
// ffffffff92c5c611:	00 00 00 00
// ffffffff92c5c615:	48 83 c4 10          	add    $0x10,%rsp
// ffffffff92c5c619:	5b                   	pop    %rbx
// ffffffff92c5c61a:	41 5c                	pop    %r12
// ffffffff92c5c61c:	41 5d                	pop    %r13
// ffffffff92c5c61e:	41 5e                	pop    %r14
// ffffffff92c5c620:	41 5f                	pop    %r15
// ffffffff92c5c622:	5d                   	pop    %rbp
// ffffffff92c5c623:	31 c0                	xor    %eax,%eax
// ffffffff92c5c625:	31 d2                	xor    %edx,%edx
// ffffffff92c5c627:	31 c9                	xor    %ecx,%ecx
// ffffffff92c5c629:	31 f6                	xor    %esi,%esi
// ffffffff92c5c62b:	31 ff                	xor    %edi,%edi
// ffffffff92c5c62d:	c3                   	ret
// ffffffff92c5c62e:	cc                   	int3
// ffffffff92c5c62f:	cc                   	int3
// ffffffff92c5c630:	cc                   	int3
// ffffffff92c5c631:	cc                   	int3
// ffffffff92c5c632:	48 89 8b c8 0d 00 00 	mov    %rcx,0xdc8(%rbx)    // (3)
// ffffffff92c5c639:	eb cf                	jmp    0xffffffff92c5c60a  // 0x209

// (Maybe outdated in the new kernel. Didn't check.)
//
// The probes are placed too close to each other. As a result, even though
// only *one* of the two load instructions is executed each time, the
// handler after the 1st load is always executed.
//
//   1:   jb 5
//   2:   mov           # the 1st store of interest
//   3:   mov           # patched to jmp
//   4:   jmp elsewhere
//   5:   mov           # the 2nd store of interest
//   6:   jmp 3         # patched to int3
//

bool the_second_store;

// (1)
SEC("kprobe/ttwu_do_activate+0x1a8")
int BPF_KPROBE(ttwu_do_activate_0x1a8, struct rq *rq, struct task_struct *p, int wake_flags,
		 struct rq_flags *rf)
{
    u16 id = bpf_get_smp_processor_id();
    if (id == CPU_IDX) {
        bpf_printk("\n");
        bpf_printk("ctx->si: %lu (previous avg_idle)", ctx->si);
        the_second_store = false;
    }
    return 0;
}

// (2)
SEC("kprobe/ttwu_do_activate+0x1da")
int BPF_KPROBE(ttwu_do_activate_0x1da, struct rq *rq, struct task_struct *p, int wake_flags,
		 struct rq_flags *rf)
{
    u16 id = bpf_get_smp_processor_id();
    if (id == CPU_IDX && !the_second_store) {
        bpf_printk("ctx->ax: %lu (updated avg_idle)", ctx->ax);
    }
    return 0;
}

// (3)
SEC("kprobe/ttwu_do_activate+0x209")
int BPF_KPROBE(ttwu_do_activate_0x209, struct rq *rq, struct task_struct *p, int wake_flags,
		 struct rq_flags *rf)
{
    u16 id = bpf_get_smp_processor_id();
    if (id == CPU_IDX) {
        bpf_printk("ctx->cx: %lu (updated avg_idle)", ctx->cx);
        the_second_store = true;
    }
    return 0;
}

// (4)
SEC("kprobe/ttwu_do_activate+0x1cb")
int BPF_KPROBE(ttwu_do_activate_0x1cb, struct rq *rq, struct task_struct *p, int wake_flags,
		 struct rq_flags *rf)
{
    u16 id = bpf_get_smp_processor_id();
    if (id == CPU_IDX) {
        // manipulate diff which is signed 64-bit integer
        s64 rax = BPF_RAX(ctx);
        bool is_neg = rax < 0;
        u64 abs_rax = is_neg ? -rax : rax;
        // abs_rax /= 100;
        rax = is_neg ? -abs_rax : abs_rax;
        kfuncs_probe_write_kernel(&ctx->ax, sizeof(rax), &rax, sizeof(rax));
        bpf_printk("ctx->ax: %ld (diff)", ctx->ax);
    }
    return 0;
}
