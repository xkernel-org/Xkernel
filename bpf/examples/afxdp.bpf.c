// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#define MAX_PER_SOCKET_BUDGET 32
#define NEW_MAX_PER_SOCKET_BUDGET 8

SEC("kprobe/xsk_tx_peek_desc+0x44")
int BPF_KPROBE(xsk_tx_peek_desc_0x44) {

  // Read value from 0x358(%r12)
  u64 r12 = BPF_R12(ctx);
  u64 *addr = (u64 *)(r12 + 0x358);
  u64 val;

  if (bpf_probe_read_kernel(&val, sizeof(val), addr)) return 0;

  if (val >= NEW_MAX_PER_SOCKET_BUDGET) {
    BPF_SET_JA_TRUE(ctx);
  }

  return 0;
}
