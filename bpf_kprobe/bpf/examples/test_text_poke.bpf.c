// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

// (+0xc8)ffffffffac78ae58:        83 f8 0a                cmp    $0xa,%eax --> cmp    $0xb,%eax

ONE_SHOT_ENV(
    0xffffffffac78ae58, // instruction address
    3                   // instruction size
);

BPF_ONESHOT_INIT(test_text_poke) {
    
    BPF_PRINT_INSN("Old instruction");
    
    unsigned char new_insn[] = {0x83, 0xf8, 0x0b};
    BPF_WRITE_INSN(new_insn);

    BPF_PRINT_INSN("New instruction");

    return 0;
}

BPF_ONESHOT_EXIT(test_text_poke) {
    
    BPF_RESTORE_INSN();

    BPF_PRINT_INSN("Restored instruction");

    return 0;
}