// SPDX-License-Identifier: GPL-2.0
//
// X-tune policy: Application-informed RocksDB tuning (Paper Fig. 23)
//
// RocksDB threads with random-read patterns expose their thread IDs through
// a BPF map. This X-tune leverages the hint to set BLK_MAX_REQUEST_COUNT=1
// for those threads (bypassing plug merging), while keeping the default for
// other threads.
//
// Usage:
//   ./xkernel-tool build tunables/all.toml   # Build BLK_MAX_REQUEST_COUNT
//   # Load with: sudo ./xkernel-tool load 1 <ConstID>
//
// This corresponds to Figure 23 in the paper.

#include "xtune_stub_9.bpf.h"  // Replace with actual BLK_MAX_REQUEST_COUNT stub

#define MAX_ROCKSDB_THREADS 16

// Hint map: filled by RocksDB threads to signal random-read patterns.
// Key: PID of the thread. Value: hint flag (1 = random-read).
// RocksDB populates this via a userspace BPF map update.
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ROCKSDB_THREADS);
    __type(key, u32);
    __type(value, int);
} rocksdb_hint_map SEC(".maps");

X_TUNE_0(blk_add_rq_to_plug, "+0x42") {
    // 1. Safety guard (mandatory)
    if (!x_transition_done(x_ctx)) return 0;

    // 2. Check if the current thread is a RocksDB random-read thread
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid & 0xFFFFFFFF;

    int *hint = bpf_map_lookup_elem(&rocksdb_hint_map, &pid);
    if (hint) {
        // Random-read thread: disable plug merging (set count to 1)
        x_set(x_ctx, 1);
    }
    // Non-RocksDB threads: keep default (32) by not calling x_set

    return 0;
}
