#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include "xkernel.bpf.h"

// Guard: __pfx_perf_trace_mm_shrink_slab_end+0x10 (SS entry)
SEC("kprobe/__pfx_perf_trace_mm_shrink_slab_end+0x10")
int BPF_KPROBE(__xk_guard___pfx_perf_trace_mm_shrink_slab_end_10) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: __pfx_perf_trace_mm_shrink_slab_end+0x15145 (SS exit)
SEC("kprobe/__pfx_perf_trace_mm_shrink_slab_end+0x15145")
int BPF_KPROBE(__xk_unguard___pfx_perf_trace_mm_shrink_slab_end_15145) {
    ss_unguard_handler(ctx);
    return 0;
}

#endif
