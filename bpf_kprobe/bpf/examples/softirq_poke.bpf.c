// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// (+0x25)ffffffffb218adb5:        4c 8d 68 02             lea    0x2(%rax),%r13
#define NEW_MAX_SOFTIRQ_TIME 0x04

ONE_SHOT_ENV(
    0xffffffffb218adb5, // instruction address
    4                   // instruction size
);

BPF_ONESHOT_INIT(test_text_poke) {
    
    BPF_PRINT_INSN("Old instruction");
    
    unsigned char new_insn[] = {0x4c, 0x8d, 0x68, NEW_MAX_SOFTIRQ_TIME};
    BPF_WRITE_INSN(new_insn);

    BPF_PRINT_INSN("New instruction");

    return 0;
}

BPF_ONESHOT_EXIT(test_text_poke) {
    
    BPF_RESTORE_INSN();

    BPF_PRINT_INSN("Restored instruction");

    return 0;
}