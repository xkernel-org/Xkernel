// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/handle_softirqs+0x54")
int BPF_KPROBE(handle_softirqs) {

  // Last instruction: movl   $0xa,-0x40(%rbp)
  // Modify -0x40(%rbp) to 0x4
  u64 rbp = BPF_RBP(ctx);
  u64 *addr = (u64 *)(rbp - 0x40);
  u64 value;
  bpf_probe_read_kernel(&value, sizeof(u64), addr);

  if (value == 0xa) {
    value = 0x1;
    bpf_probe_read_kernel(addr, sizeof(u64), &value);
  }

  return 0;
}
