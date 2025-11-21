// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_endian.h>

#include "xkernel.bpf.h"

// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 1.29527 s, 4.0 MB/s

//  Performance counter stats for 'taskset -c 5 dd if=/dev/zero of=/dev/null bs=1 count=5M':

//      4,731,585,499      cpu-cycles

// Empty pre-handler (int3)
// SEC("kprobe/vfs_write+0x12b")
// int BPF_KPROBE(vfs_write_0x12b) {
//   return 0;
// }

// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 3.71166 s, 1.4 MB/s

//  Performance counter stats for 'taskset -c 5 dd if=/dev/zero of=/dev/null bs=1 count=5M':

//     13,558,692,018      cpu-cycles


// Empty pre-handler (jmp)
// SEC("kprobe/vfs_write+0xcd")
// int BPF_KPROBE(vfs_write_0xcd) {
//   return 0;
// }

// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 1.52608 s, 3.4 MB/s

//  Performance counter stats for 'taskset -c 5 dd if=/dev/zero of=/dev/null bs=1 count=5M':

// 5,569,297,053      cpu-cycles 


// (int3) xkernel + transition
// SEC("kprobe/vfs_write+0x12b")
// int BPF_KPROBE(vfs_write_0x12b) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   return 0;
// }
// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 3.77061 s, 1.4 MB/s

//  Performance counter stats for 'taskset -c 5 dd if=/dev/zero of=/dev/null bs=1 count=5M':

// 13,761,198,800      cpu-cycles 


// (jmp) xkernel + transition
// SEC("kprobe/vfs_write+0xcd")
// int BPF_KPROBE(vfs_write_0xcd) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   return 0;
// }

// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 1.56944 s, 3.3 MB/s

//  Performance counter stats for 'taskset -c 5 dd if=/dev/zero of=/dev/null bs=1 count=5M':

// 5,729,293,315      cpu-cycles

// (int3) xkernel + transition + SIE
// SEC("kprobe/vfs_write+0x12b")
// int BPF_KPROBE(vfs_write_0x12b) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value
//   return 0;
// }

// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 3.84008 s, 1.4 MB/s

// Performance counter stats for 'taskset -c 5 dd if=/dev/zero of=/dev/null bs=1 count=5M':

// 14,006,749,736      cpu-cycles 


// (jmp) xkernel + transition + SIE
// SEC("kprobe/vfs_write+0xcd")
// int BPF_KPROBE(vfs_write_0xcd) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value
//   return 0;
// }

// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 1.59919 s, 3.3 MB/s

// Performance counter stats for 'taskset -c 5 dd if=/dev/zero of=/dev/null bs=1 count=5M':

// 5,832,858,342      cpu-cycles

// (int3) xkernel + transition + SIE + probe_read
// SEC("kprobe/vfs_write+0x12b")
// int BPF_KPROBE(vfs_write_0x12b, struct file *file) {
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

// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 3.80442 s, 1.4 MB/s

// Performance counter stats for 'dd if=/dev/zero of=/dev/null bs=1 count=5M':

// 13,976,599,953      cpu-cycles


// (jmp) xkernel + transition + SIE + probe_read
// SEC("kprobe/vfs_write+0xcd")
// int BPF_KPROBE(vfs_write_0xcd, struct file *file) {
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

// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 1.61953 s, 3.2 MB/s

//  Performance counter stats for 'dd if=/dev/zero of=/dev/null bs=1 count=5M':

//      5,928,612,076      cpu-cycles

////////////////////////////////////////////////////////////
// BPF MAP 
// struct {
//     __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
//     __uint(max_entries, 1);
//     __type(key, __u32);
//     __type(value, __u64);
// } bpf_map SEC(".maps");
////////////////////////////////////////////////////////////


// (int3) xkernel + transition + SIE + probe_read + bpf map opreation
// SEC("kprobe/vfs_write+0x12b")
// int BPF_KPROBE(vfs_write_0x12b, struct file *file) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

//   unsigned int f_flags;
//   if (bpf_probe_read_kernel(&f_flags, sizeof(f_flags), &file->f_flags) != 0) {
//     return 0;
//   }

//   __u32 key = 0;
//   __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
//   if (value == NULL) {
//     return 0;
//   }
//   *value += 1;

//   return 0;
// }

// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 3.85511 s, 1.4 MB/s

// Performance counter stats for 'dd if=/dev/zero of=/dev/null bs=1 count=5M':

// 13,992,572,813      cpu-cycles


// (jmp) xkernel + transition + SIE + probe_read + bpf map opreation
// SEC("kprobe/vfs_write+0xcd")
// int BPF_KPROBE(vfs_write_0xcd, struct file *file) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

//   unsigned int f_flags;
//   if (bpf_probe_read_kernel(&f_flags, sizeof(f_flags), &file->f_flags) != 0) {
//     return 0;
//   }

//   __u32 key = 0;
//   __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
//   if (value == NULL) {
//     return 0;
//   }
//   *value += 1;

//   return 0;
// }

// 5242880 bytes (5.2 MB, 5.0 MiB) copied, 1.63258 s, 3.2 MB/s

// Performance counter stats for 'dd if=/dev/zero of=/dev/null bs=1 count=5M':

// 5,934,660,151      cpu-cycles