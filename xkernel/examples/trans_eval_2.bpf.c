// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"
#include "cs_artifact.bpf.h"

SEC("kprobe/io_issue_sqe+0x2b")
int BPF_KPROBE(io_issue_sqe_0x2b, struct file *file) {
  if (!transition_done(ctx)) {
    return 0;
  }
  u32 eax = BPF_RAX(ctx);
  BPF_SET_RAX(ctx, eax); // keep same value

  unsigned int f_flags;
  if (bpf_probe_read_kernel(&f_flags, sizeof(f_flags), &file->f_flags) != 0) {
    return 0;
  }

  return 0;
}