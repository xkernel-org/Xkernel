// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_endian.h>

#include "xkernel.bpf.h"

struct {
  __uint(type, BPF_MAP_TYPE_ARRAY);
  __uint(max_entries, 1);
  __type(key, __u32);
  __type(value, __u64);
} start_ts_map SEC(".maps");

SEC("kprobe/tcp_sendmsg_locked+0x3be")
int BPF_KPROBE(tcp_sendmsg_locked_0x3be) {
  if (!transition_done(ctx)) {
    return 0;
  }
  return 0;
}