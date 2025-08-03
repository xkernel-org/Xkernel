// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#define NEW_NUMA_PERIOD_THRESHOLD 7

// (6.14.0-15-generic)
// $ python objdump.py --func update_task_scan_period |grep 0x7
// (+0x68)ffffffffb00601f8:        8d 40 f9                lea    -0x7(%rax),%eax
// (+0x70)ffffffffb0060200:        85 c0                   test   %eax,%eax
// (+0x72)ffffffffb0060202:        0f 4e c2                cmovle %edx,%eax
// (+0x75)ffffffffb0060205:        44 0f af e0             imul   %eax,%r12d
// (+0x79)ffffffffb0060209:        41 01 cc                add    %ecx,%r12d
// (+0x7c)ffffffffb006020c:        8b 0d 4e 4d 23 02       mov    0x2234d4e(%rip),%ecx        # 0xffffffffb2294f60
// (+0x180)ffffffffb0060310:       83 e8 07                sub    $0x7,%eax
// (+0x19b)ffffffffb006032b:       83 e8 07                sub    $0x7,%eax
// $ python objdump.py --func update_task_scan_period |grep 0x6
// (+0x6)ffffffffb0060196: 48 89 e5                mov    %rsp,%rbp
// (+0x5f)ffffffffb00601ef:        83 f8 06                cmp    $0x6,%eax
// (+0x62)ffffffffb00601f2:        0f 8e 00 01 00 00       jle    0xffffffffb00602f8
// (+0x68)ffffffffb00601f8:        8d 40 f9                lea    -0x7(%rax),%eax
// (+0x6b)ffffffffb00601fb:        ba 01 00 00 00          mov    $0x1,%edx
// (+0x17b)ffffffffb006030b:       83 f8 06                cmp    $0x6,%eax

SEC("kprobe/update_task_scan_period+0x183") // sub $0x7,%eax
int BPF_KPROBE(update_task_scan_period_0x183) {
  return 0;
}

SEC("kprobe/update_task_scan_period+0x19e") // sub $0x7,%eax
int BPF_KPROBE(update_task_scan_period_0x19e) {
  return 0;
}

SEC("kprobe/update_task_scan_period+0x62") // cmp $0x6,%eax
int BPF_KPROBE(update_task_scan_period_0x62) {
  return 0;
}

SEC("kprobe/update_task_scan_period+0x17e") // cmp $0x6,%eax
int BPF_KPROBE(update_task_scan_period_0x17e) {
  return 0;
}
