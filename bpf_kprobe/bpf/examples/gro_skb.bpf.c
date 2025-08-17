// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#define NEW_MAX_GRO_SKBS 32

SEC("kprobe/dev_gro_receive+0x53b")
int BPF_KPROBE(dev_gro_receive_0x53b) {
  u64 eax = BPF_EAX(ctx);
  bpf_printk("gro list size: %d", eax);
  if (eax >= NEW_MAX_GRO_SKBS) {
    BPF_SET_JG_TRUE(ctx);
  } else {
    BPF_SET_JG_FALSE(ctx);
  }

  return 0;
}