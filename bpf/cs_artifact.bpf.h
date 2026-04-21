#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include "xkernel.bpf.h"

// Guard: tcp_sendmsg_locked+0x0 (SS entry)
SEC("kprobe/tcp_sendmsg_locked")
int BPF_KPROBE(__xk_guard_tcp_sendmsg_locked_0) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: tcp_sendmsg_locked+0xd7e (SS exit)
SEC("kprobe/tcp_sendmsg_locked+0xd7e")
int BPF_KPROBE(__xk_unguard_tcp_sendmsg_locked_d7e) {
    ss_unguard_handler(ctx);
    return 0;
}

#endif
