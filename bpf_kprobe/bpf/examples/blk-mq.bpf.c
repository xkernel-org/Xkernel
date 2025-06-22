// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "kfuncs.bpf.h"
#include "util.bpf.h"

char LICENSE[] SEC("license") = "GPL";

SEC("kprobe/blk_mq_delay_run_hw_queue")
int BPF_KPROBE(blk_mq_delay_run_hw_queue, struct blk_mq_hw_ctx *hctx,
               unsigned long msecs) {
  if (msecs)
    bpf_printk("blk_mq_delay_run_hw_queue: %lu\n", msecs);
  return 0;
}

SEC("kprobe/blk_mq_delay_run_hw_queues")
int BPF_KPROBE(blk_mq_delay_run_hw_queues, struct request_queue *q,
               unsigned long msecs) {
  if (msecs)
    bpf_printk("blk_mq_delay_run_hw_queues: %lu\n", msecs);
  return 0;
}
