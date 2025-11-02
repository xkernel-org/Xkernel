// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

/*
(base) $ python objdump.py --func __tlb_batch_free_encoded_pages
...
(+0x20)ffffffff92f69260:        66 90                   xchg   %ax,%ax
(+0x22)ffffffff92f69262:        66 90                   xchg   %ax,%ax

a. 512 -> 0x200
   2048 -> 0x800
* (+0x24)ffffffff92f69264:        bb 00 02 00 00          mov    $0x200,%ebx
(+0x29)ffffffff92f69269:        39 d9                   cmp    %ebx,%ecx
(+0x2b)ffffffff92f6926b:        0f 46 d9                cmovbe %ecx,%ebx
...
(+0x85)ffffffff92f692c5:        39 cb                   cmp    %ecx,%ebx
(+0x87)ffffffff92f692c7:        73 b7                   jae    0xffffffff92f69280

b. 512 -> 0x1ff
   2048 -> 0x7ff
* (+0x89)ffffffff92f692c9:        3d ff 01 00 00          cmp    $0x1ff,%eax
(+0x8e)ffffffff92f692ce:        77 b0                   ja     0xffffffff92f69280
(+0x90)ffffffff92f692d0:        89 da                   mov    %ebx,%edx
...
*/

/*
--- /users/yltang/sdb/linux-6.14/BUILDO/mmu_gather_original.disas.txt   2025-10-17 06:34:27.450250881 -0400
+++ /users/yltang/sdb/linux-6.14/BUILDO/mmu_gather_recompiled.disas.txt 2025-10-17 06:34:29.549275315 -0400
@@ -151,7 +151,7 @@
  11f:  53                      push   %rbx
  120:  66 90                   xchg   %ax,%ax
  122:  66 90                   xchg   %ax,%ax
- 124:  bb 00 02 00 00          mov    $0x200,%ebx
+ 124:  bb 00 08 00 00          mov    $0x800,%ebx
  129:  39 da                   cmp    %ebx,%edx
  12b:  0f 46 da                cmovbe %edx,%ebx
  12e:  8d 43 ff                lea    -0x1(%rbx),%eax
@@ -184,7 +184,7 @@
  179:  eb 11                   jmp    18c <__tlb_batch_free_encoded_pages+0x8c>
  17b:  83 c0 01                add    $0x1,%eax
  17e:  83 c3 01                add    $0x1,%ebx
- 181:  3d ff 01 00 00          cmp    $0x1ff,%eax
+ 181:  3d ff 07 00 00          cmp    $0x7ff,%eax
  186:  77 b7                   ja     13f <__tlb_batch_free_encoded_pages+0x3f>
  188:  39 d3                   cmp    %edx,%ebx
  18a:  73 b3                   jae    13f <__tlb_batch_free_encoded_pages+0x3f>
*/

// change a
SEC("kprobe/__tlb_batch_free_encoded_pages+0x29")
int BPF_KPROBE(__tlb_batch_free_encoded_pages_0x29){
    // set to 0x800(2048)
    // set to 0x400(1024)
    BPF_SET_EBX(ctx, 0x400);
    bpf_printk("0x29\n");
    return 0;
}

// change b
SEC("kprobe/__tlb_batch_free_encoded_pages+0x8e")
int BPF_KPROBE(__tlb_batch_free_encoded_pages_0x8e){
    u64 eax = (u64)BPF_EAX(ctx);
    // set to 0x7ff(2047)
    // set to 0x3ff(1023)
    if(eax > 1023){ 
        BPF_SET_JA_TRUE(ctx); 
        bpf_printk("0x8e\n");
    }
    return 0;
}