#ifndef __CS_ARTIFACT_BPF_H__
#define __CS_ARTIFACT_BPF_H__

#include "xkernel.bpf.h"

// Guard: migrate_pages+0x872 (SS entry)
SEC("kprobe/migrate_pages+0x872")
int BPF_KPROBE(__xk_guard_migrate_pages_872) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: migrate_pages+0x877 (SS exit)
SEC("kprobe/migrate_pages+0x877")
int BPF_KPROBE(__xk_unguard_migrate_pages_877) {
    ss_unguard_handler(ctx);
    return 0;
}

// Guard: migrate_pages+0x8c4 (SS entry)
SEC("kprobe/migrate_pages+0x8c4")
int BPF_KPROBE(__xk_guard_migrate_pages_8c4) {
    ss_guard_handler(ctx);
    return 0;
}

// Unguard: migrate_pages+0x8ca (SS exit)
SEC("kprobe/migrate_pages+0x8ca")
int BPF_KPROBE(__xk_unguard_migrate_pages_8ca) {
    ss_unguard_handler(ctx);
    return 0;
}

#endif
