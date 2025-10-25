// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/tcp_rack_detect_loss+0x6a")
int BPF_KPROBE(tcp_rack_detect_loss_6a) {

  if (!transition_done()) {
    return 0;
  }

  u64 r15d = BPF_R15(ctx);
  BPF_SET_R15(ctx, r15d << 1);
  return 0;
}