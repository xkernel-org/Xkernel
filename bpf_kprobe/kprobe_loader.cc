// SPDX-License-Identifier: GPL-2.0
#include <bpf/libbpf.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>

#include "loader_common.h"

using namespace xkernel;

// #define BPF_FILE "bpf/examples/cubic.bpf.o"
// #define BPF_FILE "bpf/examples/gro_skb.bpf.o"
// #define BPF_FILE "bpf/examples/io_uring.bpf.o"
#define BPF_FILE "bpf/examples/blk-mq.bpf.o"

int main() {
  XKernelLoader loader(BPF_FILE);

  if (loader.attach_all_progs()) {
    fprintf(stderr, "Failed to attach all programs\n");
    return 1;
  }

  printf(
      "Kprobe attached successfully. Check /sys/kernel/tracing/trace_pipe\n");
  while (1)
    sleep(1);
}