// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/ksys_mmap_pgoff+0x43")
int BPF_KPROBE(ksys_mmap_pgoff_43) {

  if (!transition_done()) {
    bpf_printk("Transition not done");
    return 0;
  }

  bpf_printk("Transition done");
  return 0;
}