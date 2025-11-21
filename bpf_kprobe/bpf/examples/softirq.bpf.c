// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#define MAX_SOFTIRQ_RESTART 1

SEC("kprobe/handle_softirqs+0x54")
int BPF_KPROBE(handle_softirqs) {

  // Last instruction: movl   $0xa,-0x40(%rbp)
  // Modify -0x40(%rbp) 
  u64 rbp = BPF_RBP(ctx);
  u64 *addr = (u64 *)(rbp - 0x40);
  u64 value;
  if (bpf_probe_read_kernel(&value, sizeof(u64), addr) != 0) {
    return 0;
  }

  value = MAX_SOFTIRQ_RESTART;
  bpf_probe_write_kernel(addr, sizeof(u64), &value);

  return 0;
}

// #define MAX_SOFTIRQ_TIME 2
// #define NEW_MAX_SOFTIRQ_TIME 1

// SEC("kprobe/handle_softirqs+0x37")
// int BPF_KPROBE(handle_softirqs_0x37) {

//   // Last instruction: lea    0x2(%rax),%r15
//   // Modify %r15
//   u64 r15 = BPF_R15(ctx);
//   BPF_SET_R15(ctx, r15 + (NEW_MAX_SOFTIRQ_TIME - MAX_SOFTIRQ_TIME));


//   return 0;
// }
