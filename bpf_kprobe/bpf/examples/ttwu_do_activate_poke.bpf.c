// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// (+0x1c7)ffffffff9aa52257:       48 c1 f8 03             sar    $0x3,%rax

ONE_SHOT_ENV(0xffffffff9aa52257,4);

BPF_ONESHOT_INIT(ttwu_do_activate) {
  BPF_PRINT_INSN("Old instruction");
  unsigned char new_insn[] = {0x48, 0xc1, 0xf8, 0x02};
  BPF_WRITE_INSN(new_insn);
  BPF_PRINT_INSN("New instruction");
  return 0;
}

BPF_ONESHOT_EXIT(ttwu_do_activate) {
  BPF_RESTORE_INSN();
  BPF_PRINT_INSN("Restored instruction");
  return 0;
}
