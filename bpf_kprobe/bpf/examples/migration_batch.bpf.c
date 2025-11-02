// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

/* Modify target value here: 
*  origin   1024 / 512 / 256 / 128 / 64 / 32 / ...
*  eax  >   1023 / 511 / 255 / 127 / 63 / 31 ...
*  jump condition:
*  OF = SF && ZF = 0
*/

SEC("kprobe/migrate_pages+0x117")
int BPF_KPROBE(migrate_pages_0x117){
    int eax = (int)BPF_EAX(ctx);
    /* Modify it here */
    if(eax > 1023){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x117\n");
    }
    return 0;
}

SEC("kprobe/migrate_pages+0x164")
int BPF_KPROBE(migrate_pages_0x164){
    int eax = (int)BPF_EAX(ctx);
    if(eax > 1023){
        BPF_SET_JG_TRUE(ctx);
        bpf_printk("0x164\n");
    }
    return 0;
}