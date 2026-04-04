// SPDX-License-Identifier: GPL-2.0
//
// X-tune policy: Adaptive BLK_MAX_REQUEST_COUNT via merge failure tracking (Paper Fig. 25)
//
// Instruments blk_attempt_plug_merge() to track historical merge failures.
// When the failure rate exceeds a threshold, reduces BLK_MAX_REQUEST_COUNT
// to avoid wasting CPU on futile merge attempts.
//
// Usage:
//   ./xkernel-tool build tunables/all.toml   # Build BLK_MAX_REQUEST_COUNT
//   # Load with: sudo ./xkernel-tool load 1 <ConstID>
//
// This corresponds to Figure 25 in the paper.

#include "xtune_stub_9.bpf.h"  // Replace with actual BLK_MAX_REQUEST_COUNT stub

#define MERGE_FAIL_THRESHOLD 16

// Per-task storage for tracking consecutive merge failures.
struct {
    __uint(type, BPF_MAP_TYPE_TASK_STORAGE);
    __uint(map_flags, BPF_F_NO_PREALLOC);
    __type(key, int);
    __type(value, int);
} merge_fail_map SEC(".maps");

// Auxiliary kretprobe: track merge outcomes from blk_attempt_plug_merge()
SEC("kretprobe/blk_attempt_plug_merge")
int BPF_KRETPROBE(blk_attempt_plug_merge_ret, long ret) {
    struct task_struct *task = bpf_get_current_task_btf();
    int *fail_cnt = bpf_task_storage_get(&merge_fail_map, task, NULL,
                                          BPF_LOCAL_STORAGE_GET_F_CREATE);
    if (!fail_cnt)
        return 0;

    if (ret == 0)
        (*fail_cnt)++;   // Merge failed
    else
        *fail_cnt = 0;   // Merge succeeded: reset counter

    return 0;
}

// Main X-tune: use failure count to decide batch size
X_TUNE_0(blk_add_rq_to_plug, "+0x42") {
    // 1. Safety guard (mandatory)
    if (!x_transition_done(x_ctx)) return 0;

    // 2. Check merge failure history for this task
    struct task_struct *task = bpf_get_current_task_btf();
    int *fail_cnt = bpf_task_storage_get(&merge_fail_map, task, NULL, 0);

    if (fail_cnt && *fail_cnt >= MERGE_FAIL_THRESHOLD) {
        // High failure rate: reduce batch size to avoid wasted merge attempts
        x_set(x_ctx, 4);
    }
    // else: keep default (32)

    return 0;
}
