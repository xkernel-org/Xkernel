// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/smc_tx_sndbuf_nonempty+0x2bf")
int BPF_KPROBE(smc_tx_sndbuf_nonempty) {

  bpf_printk("smc_tx_sndbuf_nonempty");
  return 0;
}

SEC("kprobe/smc_tx_consumer_update+0x163")
int BPF_KPROBE(smc_tx_consumer_update) {

  bpf_printk("smc_tx_consumer_update");
  return 0;
}
