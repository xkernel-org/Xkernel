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

#define NEW_BLK_PLUG_FLUSH_SIZE (256 * 1024)

// (+0x12e)ffffffff9d5d923e:       41 81 7d 2c ff ff 01    cmpl   $0x1ffff,0x2c(%r13)
// if 0x2c(%r13) <= 0x1ffff, then jump
SEC("kprobe/blk_add_rq_to_plug+0x136")
int BPF_KPROBE(blk_add_rq_to_plug_0x136, struct blk_plug *plug, struct request *rq) {
  // read contents from 0x2c(%r13)
  u64 r13 = BPF_R13(ctx);
  u64 *addr = (u64 *)(r13 + 0x2c);
  u32 rq_bytes;
  if (bpf_probe_read_kernel(&rq_bytes, sizeof(u32), addr)) {
    return 0;
  }

  // bpf_printk("rq_bytes: %lu", rq_bytes);

  if (rq_bytes < NEW_BLK_PLUG_FLUSH_SIZE) {
    BPF_SET_JBE_TRUE(ctx);
  } else {
    BPF_SET_JBE_FALSE(ctx);
  }
  return 0;
}
