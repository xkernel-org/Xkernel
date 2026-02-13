// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#define KFREE_DRAIN_JIFFIES 5000 // 5 * HZ
#define NEW_KFREE_DRAIN_JIFFIES 500

SEC(".bss.print_cnt")
u64 print_cnt = 0;

SEC("kprobe/__schedule_delayed_monitor_work+0x4b")
int BPF_KPROBE(__schedule_delayed_monitor_work_0x4b) {

  u64 value = NEW_KFREE_DRAIN_JIFFIES;
  BPF_SET_RCX(ctx, value);

  // read and print rcx
  u64 delay = BPF_RCX(ctx);
  u64 delay_left = BPF_RAX(ctx);
  bpf_printk("[%d] delay: %llu, delay_left: %llu\n", ++print_cnt, delay, delay_left);

  return 0;
}
