#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include "xkernel.bpf.h"

// Guard: blk_start_plug_nr_ios+0x29 (SS entry)
SEC("kprobe/blk_start_plug_nr_ios+0x29")
int BPF_KPROBE(__xk_guard_blk_start_plug_nr_ios_29) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: blk_start_plug_nr_ios+0x584 (SS exit)
SEC("kprobe/blk_start_plug_nr_ios+0x584")
int BPF_KPROBE(__xk_unguard_blk_start_plug_nr_ios_584) {
    ss_unguard_handler(ctx);
    return 0;
}

// Guard: blk_add_rq_to_plug+0xd1 (SS entry)
SEC("kprobe/blk_add_rq_to_plug+0xd1")
int BPF_KPROBE(__xk_guard_blk_add_rq_to_plug_d1) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: blk_add_rq_to_plug+0xd5 (SS exit)
SEC("kprobe/blk_add_rq_to_plug+0xd5")
int BPF_KPROBE(__xk_unguard_blk_add_rq_to_plug_d5) {
    ss_unguard_handler(ctx);
    return 0;
}

#endif
