// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

/** source code
 * Plug flush limits
#define BLK_MAX_REQUEST_COUNT	32
#define BLK_PLUG_FLUSH_SIZE	(128 * 1024)
 **/

#define NEW_BLK_MAX_REQUEST_COUNT (128)
// #define NEW_BLK_PLUG_FLUSH_SIZE (2048 * 1024)

// SEC("kprobe/blk_add_rq_to_plug")
// int BPF_KPROBE(blk_add_rq_to_plug, struct blk_plug *plug, struct request *rq) {
//   return 0;
// }

// SEC("kprobe/blk_mq_flush_plug_list")
// int BPF_KPROBE(blk_mq_flush_plug_list, struct blk_plug *plug, bool from_schedule) {
//   u16 rq_count;
//   bpf_probe_read_kernel(&rq_count, sizeof(u16), &plug->rq_count);
//   if (rq_count)
//     bpf_printk("plug->rq_count = %d", rq_count);
//   return 0;
// }

SEC("kprobe/blk_add_rq_to_plug+0x118")
int BPF_KPROBE(blk_add_rq_to_plug_0x118, struct blk_plug *plug, struct request *rq) {
  BPF_SET_EAX(ctx, NEW_BLK_MAX_REQUEST_COUNT);
  // u16 r15 = BPF_R15(ctx);
  // u16 ax = BPF_AX(ctx);
  // LOG_CPU("ax = %d, r15 = %d", ax, r15);
  return 0;
}
