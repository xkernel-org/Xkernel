// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#define BLK_MQ_CPU_WORK_BATCH 8
#define NEW_BLK_MQ_CPU_WORK_BATCH 1

// SEC("kprobe/blk_mq_delay_run_hw_queue+0x12")
SEC("kprobe/blk_mq_delay_run_hw_queue+0xbf")
int BPF_KPROBE(blk_mq_delay_run_hw_queue_0xbf, struct blk_mq_hw_ctx *hctx,
               unsigned long msecs) {

  LOG_CPU("hctx: %p, msecs: %lu", hctx, msecs);
  return 0;
# if 0
  // movl   $0x8,0xa4(%rbx)
  u64 rbx = BPF_RBX(ctx);
  u64 *addr = (u64 *)(rbx + 0xa4);
  u64 val;
  
  if (bpf_probe_read_kernel(&val, sizeof(val), addr)) return 0;

  if ((val & BPF_32BIT_MASK) == BLK_MQ_CPU_WORK_BATCH) {
    val &= 0xffffffff00000000;
    val |= NEW_BLK_MQ_CPU_WORK_BATCH;
    kfuncs_probe_write_kernel(addr, sizeof(val), &val, sizeof(val));
  }
#endif

  return 0;
}