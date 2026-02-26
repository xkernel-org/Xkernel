#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/blk_mq_delay_run_hw_queue+0xcf")
int BPF_KPROBE(blk_mq_delay_run_hw_queue_cf) {
    per_task_transition_handler(ctx);
    return 0;
}

SEC("kprobe/blk_mq_map_swqueue+0x41c")
int BPF_KPROBE(blk_mq_map_swqueue_41c) {
    per_task_transition_handler(ctx);
    return 0;
}

#endif
