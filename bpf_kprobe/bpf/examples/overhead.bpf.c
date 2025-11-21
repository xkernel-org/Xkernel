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

// (int3) xkernel + transition + SIE + probe_read
// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 7.47469 s, 701 kB/s

// Performance counter stats for 'dd if=/dev/zero of=/dev/null bs=1 count=5M':

// 24,474,541,226      cpu-cycles 
// SEC("kprobe/vfs_write+0x11a")
// int BPF_KPROBE(vfs_write_0x11a, struct file *file) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

//   unsigned int f_flags;
//   if (bpf_probe_read_kernel(&f_flags, sizeof(f_flags), &file->f_flags) != 0) {
//     return 0;
//   }

//   return 0;
// }


// (jmp) xkernel + transition + SIE + probe_read
// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 5.01344 s, 1.0 MB/s

// Performance counter stats for 'dd if=/dev/zero of=/dev/null bs=1 count=5M':

// 16,353,451,933      cpu-cycles
// SEC("kprobe/vfs_write+0xc7")
// int BPF_KPROBE(vfs_write_0xc7, struct file *file) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

//   unsigned int f_flags;
//   if (bpf_probe_read_kernel(&f_flags, sizeof(f_flags), &file->f_flags) != 0) {
//     return 0;
//   }

//   return 0;
// }


////////////////////////////////////////////////////////////
// BPF MAP 
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} bpf_map SEC(".maps");
////////////////////////////////////////////////////////////


// (int3) xkernel + transition + SIE + probe_read + bpf map operation
// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 7.65247 s, 685 kB/s

//  Performance counter stats for 'dd if=/dev/zero of=/dev/null bs=1 count=5M':

//     24,893,176,700      cpu-cycles
// SEC("kprobe/vfs_write+0x11a")
// int BPF_KPROBE(vfs_write_0x11a, struct file *file) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

//   unsigned int f_flags;
//   if (bpf_probe_read_kernel(&f_flags, sizeof(f_flags), &file->f_flags) != 0) {
//     return 0;
//   }

//     __u32 key = 0;
//   __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
//   if (value == NULL) {
//     return 0;
//   }
//   *value += 1;

//   return 0;
// }


// (jmp) xkernel + transition + SIE + probe_read + bpf map operation
// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 5.03384 s, 1.0 MB/s

//  Performance counter stats for 'dd if=/dev/zero of=/dev/null bs=1 count=5M':

//     16,455,804,950      cpu-cycles 
// SEC("kprobe/vfs_write+0xc7")
// int BPF_KPROBE(vfs_write_0xc7, struct file *file) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

//   unsigned int f_flags;
//   if (bpf_probe_read_kernel(&f_flags, sizeof(f_flags), &file->f_flags) != 0) {
//     return 0;
//   }

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }