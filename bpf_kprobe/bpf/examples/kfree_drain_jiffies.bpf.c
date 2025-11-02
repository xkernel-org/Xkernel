// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"


/*
5 -> 1
--- Diff for mm/slab_common.c ---
--- /users/yltang/sdb/linux-6.14/BUILDO/mm_slab_common_c_original.disas.txt     2025-10-28 04:04:55.915224713 -0400
+++ /users/yltang/sdb/linux-6.14/BUILDO/mm_slab_common_c_recompiled.disas.txt   2025-10-28 04:05:01.719259991 -0400
@@ -1311 +1311 @@
-     abc:      81 e1 87 13 00 00       and    $0x1387,%ecx
+     abc:      81 e1 e7 03 00 00       and    $0x3e7,%ecx


5 -> 3
--- /users/yltang/sdb/linux-6.14/BUILDO/mm_slab_common_c_original.disas.txt     2025-10-28 04:06:33.015951705 -0400
+++ /users/yltang/sdb/linux-6.14/BUILDO/mm_slab_common_c_recompiled.disas.txt   2025-10-28 04:06:38.867068236 -0400
@@ -1311 +1311 @@
-     abc:      81 e1 87 13 00 00       and    $0x1387,%ecx
+     abc:      81 e1 b7 0b 00 00       and    $0xbb7,%ecx
*/

SEC("kprobe/__schedule_delayed_monitor_work+0x32")
int BPF_KPROBE(__schedule_delayed_monitor_work_0x32){
    BPF_SET_ECX(ctx, 0x3e7); 
    // BPF_SET_ECX(ctx, 0xbb7);
    bpf_printk("0x3e7\n");
    return 0;
}