#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/__blk_mq_sched_dispatch_requests+0x595")
int BPF_KPROBE(__blk_mq_sched_dispatch_requests_595) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/__blk_mq_sched_dispatch_requests+0x5b3")
int BPF_KPROBE(__blk_mq_sched_dispatch_requests_5b3) {
    per_task_transition_handler(ctx);
    return 0;
}

#endif
