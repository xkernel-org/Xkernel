// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#define BLK_MQ_CPU_WORK_BATCH 0x8
#define NEW_BLK_MQ_CPU_WORK_BATCH 0x32

// (+0xbf)ffffffff848898bf:        c7 83 a4 00 00 00 08    movl   $0x8,0xa4(%rbx)

ONE_SHOT_ENV(0xffffffff848898bf,7);

BPF_ONESHOT_INIT(blk_mq_cpu_work_batch) {
  BPF_PRINT_INSN("Old instruction");
  unsigned char new_insn[] = {0xc7, 0x83, 0xa4, 0x00, 0x00, 0x00, NEW_BLK_MQ_CPU_WORK_BATCH};
  BPF_WRITE_INSN(new_insn);
  BPF_PRINT_INSN("New instruction");
  return 0;
}

BPF_ONESHOT_EXIT(blk_mq_cpu_work_batch) {
  BPF_RESTORE_INSN();
  BPF_PRINT_INSN("Restored instruction");
  return 0;
}
