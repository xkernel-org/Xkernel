// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC(".bss");
void *target_addr;
char old_insn[5];

BPF_ONESHOT_INIT(test_text_poke) {
    // (+0x52)ffffffff9d18ade2:        bb 0a 00 00 00          mov    $0xa,%ebx
    // (+0x57)ffffffff9d18ade7:        44 89 65 b4             mov    %r12d,-0x4c(%rbp)
    target_addr = (void *)0xffffffff9d18ade2;
    
    if (bpf_probe_read_kernel(old_insn, sizeof(old_insn), target_addr)) return 1;
    LOG_INSN_5(old_insn, "old_insn");
    
    char new_insn[5] = {0xbb, 0x05, 0x00, 0x00, 0x00};
    kfuncs_text_poke(target_addr, new_insn, sizeof(new_insn));

    LOG_INSN_5(new_insn, "new_insn");

    return 0;
}

BPF_ONESHOT_EXIT(test_text_poke) {
    kfuncs_text_poke(target_addr, old_insn, sizeof(old_insn));

    char new_insn[5];
    if (bpf_probe_read_kernel(new_insn, sizeof(new_insn), target_addr)) return 1;
    LOG_INSN_5(new_insn, "restored_insn");

    return 0;
}