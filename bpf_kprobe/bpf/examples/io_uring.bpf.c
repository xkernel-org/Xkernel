// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "kfuncs.bpf.h"
#include "util.bpf.h"

char LICENSE[] SEC("license") = "GPL";

#define IO_LOCAL_TW_DEFAULT_MAX 4

SEC("kprobe/io_cqring_wait+0x7A")
int BPF_KPROBE(io_cqring_wait_0x7A) {
  BPF_SET_ECX(ctx, IO_LOCAL_TW_DEFAULT_MAX);
  return 0;
}

SEC("kprobe/io_run_task_work_sig+0x53")
int BPF_KPROBE(io_run_task_work_sig_0x53) {
  BPF_SET_ECX(ctx, IO_LOCAL_TW_DEFAULT_MAX);
  return 0;
}
