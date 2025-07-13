// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#define NEW_NUMA_PERIOD_THRESHOLD 7

// chenzj@node-0:~/Xkernel$ python objdump.py --func update_task_scan_period |grep 0x7
// (+0x70)ffffffffb3566260:        83 ee 07                sub    $0x7,%esi
// (+0x73)ffffffffb3566263:        0f 85 1e 01 00 00       jne    0xffffffffb3566387
// (+0x79)ffffffffb3566269:        45 8d 34 08             lea    (%r8,%rcx,1),%r14d
// (+0x7d)ffffffffb356626d:        8b 0d 95 47 53 02       mov    0x2534795(%rip),%ecx        # 0xffffffffb5a9aa08
// (+0x194)ffffffffb3566384:       83 ee 07                sub    $0x7,%esi
// (+0x1a0)ffffffffb3566390:       83 e8 07                sub    $0x7,%eax
// chenzj@node-0:~/Xkernel$ python objdump.py --func update_task_scan_period |grep 0x6
// (+0x6)ffffffffb35661f6:         48 89 e5                mov    %rsp,%rbp
// (+0x60)ffffffffb3566250:        49 c1 e8 23             shr    $0x23,%r8
// (+0x64)ffffffffb3566254:        48 89 c6                mov    %rax,%rsi
// (+0x67)ffffffffb3566257:        83 f8 06                cmp    $0x6,%eax
// (+0x6a)ffffffffb356625a:        0f 8e 0b 01 00 00       jle    0xffffffffb356636b
// (+0x18a)ffffffffb356637a:       83 f8 06                cmp    $0x6,%eax

SEC("kprobe/update_task_scan_period+0x73")
int BPF_KPROBE(update_task_scan_period_0x73) {
  u64 value = BPF_ESI(ctx) - 1;
  BPF_SET_ESI(ctx, value);
  return 0;
}

SEC("kprobe/update_task_scan_period+0x1a0")
int BPF_KPROBE(update_task_scan_period_0x1a0) {
  u64 value = BPF_ESI(ctx) - 1;
  BPF_SET_ESI(ctx, value);
  return 0;
}

SEC("kprobe/update_task_scan_period+0x1a3")
int BPF_KPROBE(update_task_scan_period_0x1a3) {
  u64 value = BPF_EAX(ctx) - 1;
  BPF_SET_EAX(ctx, value);
  return 0;
}

SEC("kprobe/update_task_scan_period+0x6a")
int BPF_KPROBE(update_task_scan_period_0x6a) {
  u64 eax = BPF_EAX(ctx);
  if (eax < NEW_NUMA_PERIOD_THRESHOLD - 1) {
    BPF_SET_JLE_TRUE(ctx);
  } else {
    BPF_SET_JLE_FALSE(ctx);
  }
  return 0;
}

SEC("kprobe/update_task_scan_period+0x18d")
int BPF_KPROBE(update_task_scan_period_0x18d) {
  u64 eax = BPF_EAX(ctx);
  if (eax > NEW_NUMA_PERIOD_THRESHOLD - 1) {
    BPF_SET_JG_TRUE(ctx);
  } else {
    BPF_SET_JG_FALSE(ctx);
  }
  return 0;
}
