// SPDX-License-Identifier: GPL-2.0
// BPF policy for ConstID 1 - BLK_MAX_REQUEST_COUNT

#include "xtune_stub_1.bpf.h"

// void blk_start_plug_nr_ios(struct blk_plug *plug, unsigned short nr_ios)
// Kprobe 1: blk_start_plug_nr_ios+0x25 (simple)
// Relationship: IV = V
X_TUNE_0(blk_start_plug_nr_ios, "+0x25") {
    if (!x_transition_done(x_ctx)) return 0;

    u64 val = 1; // patched value (original: 32)
    x_set(x_ctx, val);
    return 0;
}
