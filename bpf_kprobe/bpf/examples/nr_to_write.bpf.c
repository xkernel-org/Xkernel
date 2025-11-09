// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/make_free_space+0x6e")
int BPF_KPROBE(make_free_space_0x6e){
    BPF_SET_ESI(ctx, 0x20);
    bpf_printk("0x6e\n");
    return 0;
}

// sudo dd if=/dev/zero of=/mnt/ubifs/fill bs=1M count=85 conv=fsync status=progress