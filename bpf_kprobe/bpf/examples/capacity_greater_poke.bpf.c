// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#ifndef SYMBOL_BASE_ADDRESS1
#error "You must provide SYMBOL_BASE_ADDRESS1"
#endif

#ifndef SYMBOL_BASE_ADDRESS2
#error "You must provide SYMBOL_BASE_ADDRESS2"
#endif

// #ifndef NEW_VALUE
// #warning "No NEW_VALUE specified. Effectively no change."
// #define NEW_VALUE 1078
// #endif

/*

  I found these offsets with the below procedures

  1. make sure it's limited in kernel/sched/fair.o
  2. objdump -d kernel/sched/fair.o > fair.1078.disas.txt
  3. sed -i 's|#define capacity_greater(cap1, cap2) ((cap1) \* 1024 > (cap2) \* 1078)|#define capacity_greater(cap1, cap2) ((cap1) * 1024 > (cap2) * 1200)|' kernel/sched/fair.c
  4. make kernel/sched/fair.o
  5. objdump -d kernel/sched/fair.o > fair.1200.disas.txt
  6. diff fair.{1078,1200}.disas.txt

  21486,21487c21486,21487
  <    13c40:     49 69 84 04 d0 0c 00    imul   $0x436,0xcd0(%r12,%rax,1),%rax
  <    13c47:     00 36 04 00 00
  ---
  >    13c40:     49 69 84 04 d0 0c 00    imul   $0x4b0,0xcd0(%r12,%rax,1),%rax
  >    13c47:     00 b0 04 00 00
  21585c21585
  <    13e09:     48 69 52 18 36 04 00    imul   $0x436,0x18(%rdx),%rdx
  ---
  >    13e09:     48 69 52 18 b0 04 00    imul   $0x4b0,0x18(%rdx),%rdx
  22394c22394
  <    14bc9:     49 69 ce 36 04 00 00    imul   $0x436,%r14,%rcx
  ---
  >    14bc9:     49 69 ce b0 04 00 00    imul   $0x4b0,%r14,%rcx

*/

/*

  (6.14.0-export-text-poke)
  0000000000013400 <update_sd_lb_stats.constprop.0>:
      ...
      13c40:	49 69 84 04 d0 0c 00 	imul   $0x436,0xcd0(%r12,%rax,1),%rax (+0x840)
      13c47:	00 36 04 00 00
      ...
      13e09:	48 69 52 18 36 04 00 	imul   $0x436,0x18(%rdx),%rdx         (+0xa09)
  00000000000147d0 <sched_balance_rq>:
      ...
      14bc9:	49 69 ce 36 04 00 00 	imul   $0x436,%r14,%rcx               (+0x3f9)

*/

#if 0 // FIXME: why this doesn't work??

ONE_SHOT_ENV_NAMED(SYMBOL_BASE_ADDRESS1+0x840, 12, imul1);

BPF_ONESHOT_INIT(update_sd_lb_stats__imul1) {
  unsigned char new_insn[] = {0x49, 0x69, 0x84, 0x04, 0xd0, 0x0c, 0x00,
                              0x00, 0xb0, 0x04, 0x00, 0x00};
  BPF_WRITE_INSN_NAMED(new_insn, imul1);
  return 0;
}

BPF_ONESHOT_EXIT(update_sd_lb_stats__imul1) {
  BPF_RESTORE_INSN_NAMED(imul1);
  return 0;
}

#else

ONE_SHOT_ENV_NAMED(SYMBOL_BASE_ADDRESS1+0x847, 5, imul1);

BPF_ONESHOT_INIT(update_sd_lb_stats__imul1) {
  unsigned char new_insn[] = {0x00, 0xb0, 0x04, 0x00, 0x00};
  BPF_WRITE_INSN_NAMED(new_insn, imul1);
  return 0;
}

BPF_ONESHOT_EXIT(update_sd_lb_stats__imul1) {
  BPF_RESTORE_INSN_NAMED(imul1);
  return 0;
}

#endif

///////////////////////////////////////////////////////////////////////////

ONE_SHOT_ENV_NAMED(SYMBOL_BASE_ADDRESS1+0xa09, 7, imul2);

BPF_ONESHOT_INIT(update_sd_lb_stats__imul2) {
  unsigned char new_insn[] = {0x48, 0x69, 0x52, 0x18, 0xb0, 0x04, 0x00};
  BPF_WRITE_INSN_NAMED(new_insn, imul2);
  return 0;
}

BPF_ONESHOT_EXIT(update_sd_lb_stats__imul2) {
  BPF_RESTORE_INSN_NAMED(imul2);
  return 0;
}

///////////////////////////////////////////////////////////////////////////

ONE_SHOT_ENV_NAMED(SYMBOL_BASE_ADDRESS2+0x3f9, 7, imul3);

BPF_ONESHOT_INIT(sched_balance_rq__imul3) {
  unsigned char new_insn[] = {0x49, 0x69, 0xce, 0xb0, 0x04, 0x00, 0x00};
  BPF_WRITE_INSN_NAMED(new_insn, imul3);
  return 0;
}

BPF_ONESHOT_EXIT(sched_balance_rq__imul3) {
  BPF_RESTORE_INSN_NAMED(imul3);
  return 0;
}
