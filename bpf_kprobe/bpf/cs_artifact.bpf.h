#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

SEC("kprobe/io_poll_wake")
int BPF_KPROBE(io_poll_wake) {
    per_task_transition_handler(ctx);
    return 0;
}

#endif
