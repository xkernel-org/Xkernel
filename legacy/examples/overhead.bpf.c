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
// SEC("kprobe/vfs_write+0xda")
// int BPF_KPROBE(vfs_write_0xda) {
//   return 0;
// }

// Empty pre-handler (jmp)
// 1024000 bytes (1.0 MB, 1000 KiB) copied, 0.867847 s, 1.2 MB/s
// 14,158,478,575      cpu-cycles 
// SEC("kprobe/vfs_write+0xd6")
// int BPF_KPROBE(vfs_write_0xd6) {
//   return 0;
// }

// (int3) xkernel + transition
// 1024000 bytes (1.0 MB, 1000 KiB) copied, 1.41217 s, 725 kB/s
// 22,951,824,514      cpu-cycles
// SEC("kprobe/vfs_write+0xda")
// int BPF_KPROBE(vfs_write_0xda) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   return 0;
// }

// (jmp) xkernel + transition
// 1024000 bytes (1.0 MB, 1000 KiB) copied, 0.901542 s, 1.1 MB/s
// 14,881,727,061      cpu-cycles
// SEC("kprobe/vfs_write+0xd6")
// int BPF_KPROBE(vfs_write_0xd6) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   return 0;
// }

// (int3) xkernel + transition + SIE
// 1024000 bytes (1.0 MB, 1000 KiB) copied, 1.42933 s, 716 kB/s
// 23,336,820,534      cpu-cycles
// SEC("kprobe/vfs_write+0xda")
// int BPF_KPROBE(vfs_write_0xda) {
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
// SEC("kprobe/vfs_write+0xd6")
// int BPF_KPROBE(vfs_write_0xd6) {
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
// SEC("kprobe/vfs_write+0xda")
// int BPF_KPROBE(vfs_write_0xda, struct file *file) {
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
// SEC("kprobe/vfs_write+0xd6")
// int BPF_KPROBE(vfs_write_0xd6, struct file *file) {
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
// SEC("kprobe/vfs_write+0xda")
// int BPF_KPROBE(vfs_write_0xda, struct file *file) {
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
SEC("kprobe/io_issue_sqe+0x2b")
int BPF_KPROBE(io_issue_sqe_0x2b, struct file *file) {
  if (!transition_done(ctx)) {
    return 0;
  }
  u32 eax = BPF_RAX(ctx);
  BPF_SET_RAX(ctx, eax); // keep same value

  unsigned int f_flags;
  if (bpf_probe_read_kernel(&f_flags, sizeof(f_flags), &file->f_flags) != 0) {
    return 0;
  }

__u32 key = 0;
__u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
if (value == NULL) {
  return 0;
}
*value += 1;

  return 0;
}

SEC("kprobe/io_poll_issue+0x6")
int BPF_KPROBE(io_poll_issue) {
  if (!transition_done(ctx)) {
    return 0;
  }
  u32 eax = BPF_RAX(ctx);
  BPF_SET_RAX(ctx, eax); // keep same value

__u32 key = 0;
__u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
if (value == NULL) {
  return 0;
}
*value += 1;

  return 0;
}

SEC("kprobe/io_wq_submit_work+0x20")
int BPF_KPROBE(io_wq_submit_work) {
  if (!transition_done(ctx)) {
    return 0;
  }
  u32 eax = BPF_RAX(ctx);
  BPF_SET_RAX(ctx, eax); // keep same value

__u32 key = 0;
__u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
if (value == NULL) {
  return 0;
}
*value += 1;

  return 0;
}

SEC("kprobe/io_uring_cmd_prep+0x38")
int BPF_KPROBE(io_uring_cmd_prep) {
  if (!transition_done(ctx)) {
    return 0;
  }
  u32 eax = BPF_RAX(ctx);
  BPF_SET_RAX(ctx, eax); // keep same value

__u32 key = 0;
__u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
if (value == NULL) {
  return 0;
}
*value += 1;

  return 0;
}

// SEC("kprobe/io_uring_cmd+0x40")
// int BPF_KPROBE(io_uring_cmd) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

// SEC("kprobe/io_uring_cmd_mark_cancelable+0x4b")
// int BPF_KPROBE(io_uring_cmd_mark_cancelable) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

// SEC("kprobe/io_uring_try_cancel_uring_cmd+0x4a")
// int BPF_KPROBE(io_uring_try_cancel_uring_cmd) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

// SEC("kprobe/io_req_uring_cleanup+0x11")
// int BPF_KPROBE(io_req_uring_cleanup) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

// SEC("kprobe/io_poll_task_func+0x20b")
// int BPF_KPROBE(io_poll_task_func) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

// SEC("kprobe/io_poll_wake+0x13")
// int BPF_KPROBE(io_poll_wake) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

// SEC("kprobe/__io_queue_proc+0x10a")
// int BPF_KPROBE(__io_queue_proc) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

// SEC("kprobe/io_poll_queue_proc+0xd")
// int BPF_KPROBE(io_poll_queue_proc) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

// SEC("kprobe/io_poll_add_hash+0x10")
// int BPF_KPROBE(io_poll_add_hash) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

// SEC("kprobe/__io_arm_poll_handler+0xc4")
// int BPF_KPROBE(__io_arm_poll_handler) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

// SEC("kprobe/io_async_queue_proc+0x10")
// int BPF_KPROBE(io_async_queue_proc) {
//   if (!transition_done(ctx)) {
//     return 0;
//   }
//   u32 eax = BPF_RAX(ctx);
//   BPF_SET_RAX(ctx, eax); // keep same value

// __u32 key = 0;
// __u64 *value = bpf_map_lookup_elem(&bpf_map, &key);
// if (value == NULL) {
//   return 0;
// }
// *value += 1;

//   return 0;
// }

////////////////////////////////////////////////////////////
// Guard (kprobe)
////////////////////////////////////////////////////////////
SEC("kprobe/io_issue_sqe")
int BPF_KPROBE(entry_io_issue_sqe) {
  return 0;
}

SEC("kprobe/io_poll_issue")
int BPF_KPROBE(entry_io_poll_issue) {
  return 0;
}

SEC("kprobe/io_wq_submit_work")
int BPF_KPROBE(entry_io_wq_submit_work) {
  return 0;
}

SEC("kprobe/io_uring_cmd_prep")
int BPF_KPROBE(entry_io_uring_cmd_prep) {
  return 0;
}

// SEC("kprobe/io_uring_cmd")
// int BPF_KPROBE(entry_io_uring_cmd) {
//   return 0;
// }

// SEC("kprobe/io_uring_cmd_mark_cancelable")
// int BPF_KPROBE(entry_io_uring_cmd_mark_cancelable) {
//   return 0;
// }

// SEC("kprobe/io_uring_try_cancel_uring_cmd")
// int BPF_KPROBE(entry_io_uring_try_cancel_uring_cmd) {
//   return 0;
// }

// SEC("kprobe/io_req_uring_cleanup")
// int BPF_KPROBE(entry_io_req_uring_cleanup) {
//   return 0;
// }

// SEC("kprobe/io_poll_task_func")
// int BPF_KPROBE(entry_io_poll_task_func) {
//   return 0;
// }

// SEC("kprobe/io_poll_wake")
// int BPF_KPROBE(entry_io_poll_wake) {
//   return 0;
// }

// SEC("kprobe/__io_queue_proc")
// int BPF_KPROBE(entry__io_queue_proc) {
//   return 0;
// }

// SEC("kprobe/io_poll_queue_proc")
// int BPF_KPROBE(entry_io_poll_queue_proc) {
//   return 0;
// }

// SEC("kprobe/io_poll_add_hash")
// int BPF_KPROBE(entry_io_poll_add_hash) {
//   return 0;
// }

// SEC("kprobe/__io_arm_poll_handler")
// int BPF_KPROBE(entry__io_arm_poll_handler) {
//   return 0;
// }

// SEC("kprobe/io_async_queue_proc")
// int BPF_KPROBE(entry_io_async_queue_proc) {
//   return 0;
// }

////////////////////////////////////////////////////////////
// Unguard (kretprobe)
////////////////////////////////////////////////////////////

SEC("kretprobe/io_issue_sqe")
int BPF_KRETPROBE(ret_io_issue_sqe) {
  return 0;
}

SEC("kretprobe/io_poll_issue")
int BPF_KRETPROBE(ret_io_poll_issue) {
  return 0;
}

SEC("kretprobe/io_wq_submit_work")
int BPF_KRETPROBE(ret_io_wq_submit_work) {
  return 0;
}

SEC("kretprobe/io_uring_cmd_prep")
int BPF_KRETPROBE(ret_io_uring_cmd_prep) {
  return 0;
}

// SEC("kretprobe/io_uring_cmd")
// int BPF_KRETPROBE(ret_io_uring_cmd) {
//   return 0;
// }

// SEC("kretprobe/io_uring_cmd_mark_cancelable")
// int BPF_KRETPROBE(ret_io_uring_cmd_mark_cancelable) {
//   return 0;
// }

// SEC("kretprobe/io_uring_try_cancel_uring_cmd")
// int BPF_KRETPROBE(ret_io_uring_try_cancel_uring_cmd) {
//   return 0;
// }

// SEC("kretprobe/io_req_uring_cleanup")
// int BPF_KRETPROBE(ret_io_req_uring_cleanup) {
//   return 0;
// }

// SEC("kretprobe/io_poll_task_func")
// int BPF_KRETPROBE(ret_io_poll_task_func) {
//   return 0;
// }

// SEC("kretprobe/io_poll_wake")
// int BPF_KRETPROBE(ret_io_poll_wake) {
//   return 0;
// }

// SEC("kretprobe/__io_queue_proc")
// int BPF_KRETPROBE(ret__io_queue_proc) {
//   return 0;
// }

// SEC("kretprobe/io_poll_queue_proc")
// int BPF_KRETPROBE(ret_io_poll_queue_proc) {
//   return 0;
// }

// SEC("kretprobe/io_poll_add_hash")
// int BPF_KRETPROBE(ret_io_poll_add_hash) {
//   return 0;
// }

// SEC("kretprobe/__io_arm_poll_handler")
// int BPF_KRETPROBE(ret__io_arm_poll_handler) {
//   return 0;
// }

// SEC("kretprobe/io_async_queue_proc")
// int BPF_KRETPROBE(ret_io_async_queue_proc) {
//   return 0;
// }