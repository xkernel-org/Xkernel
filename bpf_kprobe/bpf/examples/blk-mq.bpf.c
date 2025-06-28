// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "kfuncs.bpf.h"
#include "util.bpf.h"

char LICENSE[] SEC("license") = "GPL";

#define BLK_MQ_CPU_WORK_BATCH 8

#define NEW_BLK_MQ_CPU_WORK_BATCH 32

SEC("kprobe/blk_mq_delay_run_hw_queue+0xbe")
int BPF_KPROBE(blk_mq_delay_run_hw_queue_0xbe, struct blk_mq_hw_ctx *hctx,
               unsigned long msecs) {
  

  // movl   $0x8,0xa4(%rbx)
  u64 rbx = BPF_RBX(ctx);
  u64 *addr = (u64 *)(rbx + 0xa4);
  u64 val;
  bpf_probe_read_kernel(&val, sizeof(val), addr);

  if ((val & 0xffffffff) == BLK_MQ_CPU_WORK_BATCH) {
    val &= 0xffffffff00000000;
    val |= NEW_BLK_MQ_CPU_WORK_BATCH;
    kfuncs_probe_write_kernel(addr, sizeof(val), &val, sizeof(val));
  }

  return 0;
}
