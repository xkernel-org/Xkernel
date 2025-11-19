// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_endian.h>

#include "xkernel.bpf.h"

// 1024000 bytes (1.0 MB, 1000 KiB) copied, 0.70355 s, 1.5 MB/s
// 11,482,245,486      cpu-cycles

// Empty pre-handler (int3)
// 1024000 bytes (1.0 MB, 1000 KiB) copied, 1.36415 s, 751 kB/s
// 22,199,889,672      cpu-cycles
// SEC("kprobe/vfs_write+0x11a")
// int BPF_KPROBE(vfs_write_0x11a) {
//   return 0;
// }

// Empty pre-handler (jmp)
// 1024000 bytes (1.0 MB, 1000 KiB) copied, 0.867847 s, 1.2 MB/s
// 14,158,478,575      cpu-cycles 
// SEC("kprobe/vfs_write+0xc7")
// int BPF_KPROBE(vfs_write_0xc7) {
//   return 0;
// }

// (int3) xkernel + transition
// 1024000 bytes (1.0 MB, 1000 KiB) copied, 1.41217 s, 725 kB/s
// 22,951,824,514      cpu-cycles
// SEC("kprobe/vfs_write+0x11a")
// int BPF_KPROBE(vfs_write_0x11a) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   return 0;
// }

// (jmp) xkernel + transition
// 1024000 bytes (1.0 MB, 1000 KiB) copied, 0.901542 s, 1.1 MB/s
// 14,881,727,061      cpu-cycles
// SEC("kprobe/vfs_write+0xc7")
// int BPF_KPROBE(vfs_write_0xc7) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   return 0;
// }

// (int3) xkernel + transition + SIE
// 1024000 bytes (1.0 MB, 1000 KiB) copied, 1.42933 s, 716 kB/s
// 23,336,820,534      cpu-cycles
// SEC("kprobe/vfs_write+0x11a")
// int BPF_KPROBE(vfs_write_0x11a) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value
//   return 0;
// }

// (jmp) xkernel + transition + SIE
// 1024000 bytes (1.0 MB, 1000 KiB) copied, 0.928121 s, 1.1 MB/s
// 15,318,634,583      cpu-cycles
// SEC("kprobe/vfs_write+0xc7")
// int BPF_KPROBE(vfs_write_0xc7) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value
//   return 0;
// }