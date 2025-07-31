// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// 4994		fits = fits_capacity(util, capacity);
// 0xffffffff9cf68ee1 <+193>:lea    (%rcx,%rcx,4),%rax
// 0xffffffff9cf68ef9 <+217>:shl    $0x8,%rax
// 0xffffffff9cf68f08 <+232>:mov    %rax,-0x50(%rbp)
// 0xffffffff9cf68fe4 <+452>:mov    0xad0(%r15,%rax,1),%rax
// 0xffffffff9cf68fec <+460>:shl    $0xa,%rax
// 0xffffffff9cf68ffd <+477>:cmp    %rax,-0x50(%rbp)
// 0xffffffff9cf69001 <+481>:setb   %al

SEC("kprobe/select_idle_capacity+0x1E1")
int BPF_KPROBE(select_idle_capacity_0x1E1) {
  
  u64 max = BPF_RAX(ctx);
  
  u64 rbp = BPF_RBP(ctx);

  // 读取 -0x50(%rbp) 的值
  u64 *cap_ptr = (u64 *)(rbp - 0x50);
  u64 cap;
  if (bpf_probe_read_kernel(&cap, sizeof(cap), cap_ptr)) return 0;

  bpf_printk("max: %lu, cap: %lu\n", max, cap);

  return 0;
}

// SEC("kprobe/select_idle_capacity")
// int BPF_KPROBE(select_idle_capacity) {
//   bpf_printk("select_idle_capacity\n");

//   return 0;
// }

// SEC("kprobe/find_energy_efficient_cpu")
// int BPF_KPROBE(find_energy_efficient_cpu) {
//   bpf_printk("find_energy_efficient_cpu\n");

//   return 0;
// }

// SEC("kprobe/pick_next_task_fair+0x2b9")
SEC("kprobe/pick_next_task_fair")
int BPF_KPROBE(pick_next_task_fair) {
    u64 max = BPF_RDX(ctx);
  
    u64 cap = BPF_RCX(ctx);
    bpf_printk("max: %lu, cap: %lu\n", max, cap);

  return 0;
}

// SEC("kprobe/select_idle_sibling+0x2c7")
// int BPF_KPROBE(select_idle_sibling_0x2c7) {
//     u64 max = BPF_RAX(ctx);
  
//     u64 cap = BPF_RDX(ctx);
//     bpf_printk("max: %lu, cap: %lu\n", max, cap);

//   return 0;
// }

// SEC("kprobe/select_idle_sibling+0x4a2")
// int BPF_KPROBE(select_idle_sibling_0x4a2) {
//     u64 max = BPF_RAX(ctx);
  
//     u64 cap = BPF_RDX(ctx);
//     bpf_printk("max: %lu, cap: %lu\n", max, cap);

//   return 0;
// }

// SEC("kprobe/select_idle_sibling+0x68e")
// int BPF_KPROBE(select_idle_sibling_0x68e) {
//     u64 max = BPF_RAX(ctx);
  
//     u64 cap = BPF_RDX(ctx);
//     bpf_printk("max: %lu, cap: %lu\n", max, cap);

//   return 0;
// }

// SEC("kprobe/select_idle_sibling+0x605")
// int BPF_KPROBE(select_idle_sibling_0x605) {
//     u64 max = BPF_RAX(ctx);
  
//     u64 cap = BPF_RDI(ctx);
//     bpf_printk("max: %lu, cap: %lu\n", max, cap);

//   return 0;
// }

