// SPDX-License-Identifier: GPL-2.0
// Auto-generated X_TUNE policy for test group 8

#include "xtune_stub_8.bpf.h"

// int migrate_pages(struct list_head * from, new_folio_t * get_new_folio, free_folio_t * put_new_folio, long unsigned int private, enum migrate_mode mode, int reason, unsigned int * ret_succeeded)
// Kprobe 1: migrate_pages+0x877 (cmp_immediate)
// Candidates: 0x877
// Relationship: IV = V + -1
X_TUNE_0(migrate_pages, "+0x877") {
    if (!x_transition_done(x_ctx)) return 0;

    // Get tunable value (V=512 originally)
    u64 val = 512; // TODO: Read from BPF map
    x_set(x_ctx, val);
    return 0;
}
