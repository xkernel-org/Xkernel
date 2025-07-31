// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// (+0xce)ffffffff97c8f87e:        83 c0 40                add    $0x40,%eax

ONE_SHOT_ENV(
  0xffffffff97c8f87e, // instruction address
  3                   // instruction size
);

BPF_ONESHOT_INIT(test_text_poke) {
  
  BPF_PRINT_INSN("Old instruction");
  
  unsigned char new_insn[] = {0x83, 0xc0, 0x21};
  BPF_WRITE_INSN(new_insn);

  BPF_PRINT_INSN("New instruction");

  return 0;
}

BPF_ONESHOT_EXIT(test_text_poke) {
  
  BPF_RESTORE_INSN();

  BPF_PRINT_INSN("Restored instruction");

  return 0;
}