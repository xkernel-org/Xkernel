// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#define NEW_MAX_GRO_SKBS 32

SEC("kprobe/dev_gro_receive+0x539")
int BPF_KPROBE(dev_gro_receive_0x539) {
  if (!transition_done(ctx)) {
    return 0;
  }
  u64 eax = BPF_EAX(ctx);
  bpf_printk("gro list size: %d", eax);
  if (eax >= NEW_MAX_GRO_SKBS) {
    BPF_SET_JG_TRUE(ctx);
  } else {
    BPF_SET_JG_FALSE(ctx);
  }

  return 0;
}

// SEC("kprobe/dev_gro_receive+0x52f")
// int BPF_KPROBE(dev_gro_receive_0x52f) {

//   // emulate lea (%rcx,%rax,8),%rdx
//   u64 rax = BPF_RAX(ctx);
//   u64 rcx = BPF_RCX(ctx);
//   u64 rdx = rcx + rax * 8;
//   BPF_SET_RDX(ctx, rdx);

//   bpf_printk("rax: %lu, rcx: %lx, rdx: %lx", rax, rcx, rdx);
  
//   // read 0x50(%rdx)
//   u64 v = 0;
//   if (bpf_probe_read_kernel(&v, sizeof(v), (void *)(BPF_RDX(ctx) + 0x50)) != 0) {
//     bpf_printk("error reading v");
//     return 0;
//   }

//   bpf_printk("rax: %lu, v: %lu", rax, v);

//   // emulate cmp 0x7, 0x50(%rdx)
//   if (v >= 8) {
//     BPF_SET_JG_TRUE(ctx);
//   } else {
//     BPF_SET_JG_FALSE(ctx);
//   }
  
//   BPF_SET_RIP(ctx, 0xffffffff9b4b0989);
//   return 0;
// }

// SEC("kprobe/dev_gro_receive+0x539")
// int BPF_KPROBE(dev_gro_receive_0x539) {
//   u64 rax = BPF_RAX(ctx);
//   u64 v = 0;
//   if (bpf_probe_read_kernel(&v, sizeof(v), (void *)(BPF_RDX(ctx) + 0x50)) != 0) {
//     return 0;
//   }
  
//   // expect v!= eax
//   // emulate mov 0x50(%rdx),%eax
//   bpf_printk("v: %lu, eax: %lu", v, rax);

//   BPF_SET_EAX(ctx,v);

//   return 0;
// }


// SEC("kprobe/dev_gro_receive+0x536")
// int BPF_KPROBE(dev_gro_receive_0x536) {
//   // BPF_SET_RIP(ctx, 0xffffffff9b4b0992);
//   BPF_SET_RIP(ctx, 0xffffffff9b4b098f);
//   u32 eflags = BPF_EFLAGS(ctx);
//   u32 eax = BPF_EAX(ctx);
//   bpf_printk("eflags: %u, eax: %u", eflags, eax);
//   return 0;
// }

// SEC("kprobe/dev_gro_receive+0x542")
// int BPF_KPROBE(dev_gro_receive_0x542) {
//   u32 rax = BPF_RAX(ctx);
//   u32 eflags = BPF_EFLAGS(ctx);
//   bpf_printk("eflags: %u", eflags);
//   bpf_printk("rax: %u", rax); // expect same
//   // BPF_SET_RAX(ctx, rax + 1);
//   return 0;
// }