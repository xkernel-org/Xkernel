
// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// (+0x52)ffffffffb218ade2:        bb 0a 00 00 00          mov    $0xa,%ebx
#define NEW_MAX_SOFTIRQ_RESTART 0x01

ONE_SHOT_ENV(
    0xffffffffb218ade2, // instruction address
    5                   // instruction size
);

BPF_ONESHOT_INIT(test_text_poke) {
    
    BPF_PRINT_INSN("Old instruction");
    
    unsigned char new_insn[] = {0xbb, NEW_MAX_SOFTIRQ_RESTART, 0x00, 0x00, 0x00};
    BPF_WRITE_INSN(new_insn);

    BPF_PRINT_INSN("New instruction");

    return 0;
}

BPF_ONESHOT_EXIT(test_text_poke) {
    
    BPF_RESTORE_INSN();

    BPF_PRINT_INSN("Restored instruction");

    return 0;
}