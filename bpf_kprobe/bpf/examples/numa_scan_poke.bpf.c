// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#ifndef SYMBOL_BASE_ADDRESS
#error "You must provide SYMBOL_BASE_ADDRESS"
#endif

#ifndef NEW_NUMA_PERIOD_THRESHOLD
#warning "No NEW_NUMA_PERIOD_THRESHOLD specified. Effectively no change."
#define NEW_NUMA_PERIOD_THRESHOLD 7
#endif

/*

  We are again seeing different inline decisions between distribution kernel
  and kernel built by ourselves.

  task_numa_fault -> task_numa_placement -> update_task_scan_period

  uname -r
  # 6.14.0-export-text-poke
  sudo cat /proc/kallsyms | grep -e ' task_numa_fault' \
    -e ' task_numa_placement' \
    -e ' update_task_scan_period'
  # ffffffff9aa612e0 T task_numa_fault

  uname -r
  # 6.14.0-15-generic
  sudo cat /proc/kallsyms | grep -e ' task_numa_fault' \
    -e ' task_numa_placement' \
    -e ' update_task_scan_period'
  # ffffffff97060190 t update_task_scan_period
  # ffffffff970638b0 t task_numa_placement
  # ffffffff9706f520 T task_numa_fault

  We previously saw this in

  select_task_rq_fair -> select_idle_sibling -> select_idle_capacity ->
    util_fits_cpu -> fits_capacity

  uname -r
  # 6.14.0-export-text-poke
  sudo cat /proc/kallsyms | grep -e ' select_task_rq_fair' \
    -e ' select_idle_sibling' \
    -e ' select_idle_capacity' \
    -e ' util_fits_cpu'
  # ffffffff9a814765 t select_task_rq_fair.cold
  # ffffffff9aa63bf0 t select_task_rq_fair

  uname -r
  # 6.14.0-15-generic
  sudo cat /proc/kallsyms | grep -e ' select_task_rq_fair' \
    -e ' select_idle_sibling' \
    -e ' select_idle_capacity' \
    -e ' util_fits_cpu'
  # ffffffff96e15f5d t select_task_rq_fair.cold
  # ffffffff970610a0 t select_idle_capacity
  # ffffffff970675c0 t select_idle_sibling
  # ffffffff970723c0 t select_task_rq_fair

  I found these offsets with the below procedures

  1. make sure it's limited in kernel/sched/fair.o
  2. objdump -d kernel/sched/fair.o > fair.7.disas.txt
  3. sed -i 's|#define NUMA_PERIOD_THRESHOLD 7|#define NUMA_PERIOD_THRESHOLD 6|' kernel/sched/fair.c
  4. make kernel/sched/fair.o
  5. objdump -d kernel/sched/fair.o > fair.6.disas.txt
  6. diff fair.{6,7}.disas.txt

  15717c15717
  <     e1e3:     83 f8 05                cmp    $0x5,%eax
  ---
  >     e1e3:     83 f8 06                cmp    $0x6,%eax
  15719c15719
  <     e1ec:     83 ee 06                sub    $0x6,%esi
  ---
  >     e1ec:     83 ee 07                sub    $0x7,%esi
  15810c15810
  <     e36f:     83 f8 05                cmp    $0x5,%eax
  ---
  >     e36f:     83 f8 06                cmp    $0x6,%eax
  15812c15812
  <     e378:     83 e8 06                sub    $0x6,%eax
  ---
  >     e378:     83 e8 07                sub    $0x7,%eax
  15892c15892
  <     e4e0:     83 e8 06                sub    $0x6,%eax
  ---
  >     e4e0:     83 e8 07                sub    $0x7,%eax

*/

/*

  (6.14.0-export-text-poke)
  000000000000d9a0 <task_numa_fault>:
      ...
      e1e3:	83 f8 06             	cmp    $0x6,%eax                            <-
      e1e6:	0f 8e 70 01 00 00    	jle    e35c <task_numa_fault+0x9bc>
      e1ec:	83 ee 07             	sub    $0x7,%esi                            <-
      ...
      e36f:	83 f8 06             	cmp    $0x6,%eax                            <-
      e372:	0f 8e 63 01 00 00    	jle    e4db <task_numa_fault+0xb3b>
      e378:	83 e8 07             	sub    $0x7,%eax                            <-
      ...
      e4e0:	83 e8 07             	sub    $0x7,%eax                            <-
      ...

*/

ONE_SHOT_ENV_NAMED(SYMBOL_BASE_ADDRESS+0x843, 3, cmp1);

BPF_ONESHOT_INIT(task_numa_fault__cmp1) {
  // BPF_PRINT_INSN("Old instruction");
  unsigned char new_insn[] = {0x83, 0xf8, NEW_NUMA_PERIOD_THRESHOLD-1};
  BPF_WRITE_INSN_NAMED(new_insn, cmp1);
  // BPF_PRINT_INSN("New instruction");
  return 0;
}

BPF_ONESHOT_EXIT(task_numa_fault__cmp1) {
  BPF_RESTORE_INSN_NAMED(cmp1);
  // BPF_PRINT_INSN("Restored instruction");
  return 0;
}

///////////////////////////////////////////////////////////////////////////

ONE_SHOT_ENV_NAMED(SYMBOL_BASE_ADDRESS+0x84c, 3, sub1);

BPF_ONESHOT_INIT(task_numa_fault__sub1) {
  unsigned char new_insn[] = {0x83, 0xee, NEW_NUMA_PERIOD_THRESHOLD};
  BPF_WRITE_INSN_NAMED(new_insn, sub1);
  return 0;
}

BPF_ONESHOT_EXIT(task_numa_fault__sub1) {
  BPF_RESTORE_INSN_NAMED(sub1);
  return 0;
}

///////////////////////////////////////////////////////////////////////////

ONE_SHOT_ENV_NAMED(SYMBOL_BASE_ADDRESS+0x9cf, 3, cmp2);

BPF_ONESHOT_INIT(task_numa_fault__cmp2) {
  unsigned char new_insn[] = {0x83, 0xf8, NEW_NUMA_PERIOD_THRESHOLD-1};
  BPF_WRITE_INSN_NAMED(new_insn, cmp2);
  return 0;
}

BPF_ONESHOT_EXIT(task_numa_fault__cmp2) {
  BPF_RESTORE_INSN_NAMED(cmp2);
  return 0;
}

///////////////////////////////////////////////////////////////////////////

ONE_SHOT_ENV_NAMED(SYMBOL_BASE_ADDRESS+0x9d8, 3, sub2);

BPF_ONESHOT_INIT(task_numa_fault__sub2) {
  unsigned char new_insn[] = {0x83, 0xee, NEW_NUMA_PERIOD_THRESHOLD};
  BPF_WRITE_INSN_NAMED(new_insn, sub2);
  return 0;
}

BPF_ONESHOT_EXIT(task_numa_fault__sub2) {
  BPF_RESTORE_INSN_NAMED(sub2);
  return 0;
}


///////////////////////////////////////////////////////////////////////////

ONE_SHOT_ENV_NAMED(SYMBOL_BASE_ADDRESS+0xb40, 3, sub3);

BPF_ONESHOT_INIT(task_numa_fault__sub3) {
  unsigned char new_insn[] = {0x83, 0xee, NEW_NUMA_PERIOD_THRESHOLD};
  BPF_WRITE_INSN_NAMED(new_insn, sub3);
  return 0;
}

BPF_ONESHOT_EXIT(task_numa_fault__sub3) {
  BPF_RESTORE_INSN_NAMED(sub3);
  return 0;
}
