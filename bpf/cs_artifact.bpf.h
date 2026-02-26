#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/cubictcp_acked+0x21a")
int BPF_KPROBE(cubictcp_acked_21a) {
    per_task_transition_handler(ctx);
    return 0;
}

#endif
