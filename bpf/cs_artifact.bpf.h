#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include "xkernel.bpf.h"

// Guard: __blk_mq_sched_dispatch_requests+0x587 (SS entry)
SEC("kprobe/__blk_mq_sched_dispatch_requests+0x587")
int BPF_KPROBE(__xk_guard___blk_mq_sched_dispatch_requests_587) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: __blk_mq_sched_dispatch_requests+0x58f (SS exit)
SEC("kprobe/__blk_mq_sched_dispatch_requests+0x58f")
int BPF_KPROBE(__xk_unguard___blk_mq_sched_dispatch_requests_58f) {
    ss_unguard_handler(ctx);
    return 0;
}

// Guard: __blk_mq_sched_dispatch_requests+0x5d4 (SS entry)
SEC("kprobe/__blk_mq_sched_dispatch_requests+0x5d4")
int BPF_KPROBE(__xk_guard___blk_mq_sched_dispatch_requests_5d4) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: __blk_mq_sched_dispatch_requests+0x5dc (SS exit)
SEC("kprobe/__blk_mq_sched_dispatch_requests+0x5dc")
int BPF_KPROBE(__xk_unguard___blk_mq_sched_dispatch_requests_5dc) {
    ss_unguard_handler(ctx);
    return 0;
}

#endif
