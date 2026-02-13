// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#include "xkernel.bpf.h"

#define container_of_const(ptr, type, member)				\
	_Generic(ptr,							\
		const typeof(*(ptr)) *: ((const type *)container_of(ptr, type, member)),\
		default: ((type *)container_of(ptr, type, member))	\
	)

#define tcp_sk(ptr) container_of_const(ptr, struct tcp_sock, inet_conn.icsk_inet.sk)

#define inet_csk(ptr) container_of_const(ptr, struct inet_connection_sock, icsk_inet.sk)

static inline void *inet_csk_ca(const struct sock *sk)
{
	return (void *)inet_csk(sk)->icsk_ca_priv;
}

// 80ms RTT
SEC("kprobe/hystart_update+0x164")
int BPF_KPROBE(hystart_update_0x164, struct sock *sk) {
  u64 eax = BPF_EAX(ctx);

  struct bictcp *ca = inet_csk_ca(sk);

  u32 curr_rtt;

  if (bpf_probe_read_kernel(&curr_rtt, sizeof(curr_rtt), &ca->curr_rtt) < 0) {
    bpf_printk("bpf_probe_read_kernel failed\n");
    return 0;
  }

  if (curr_rtt >= 60000) { // 60ms
    BPF_SET_EAX(ctx, eax << 2); // SF=1
  } else {
    // keep original value, SF=3
  }

  // BPF_SET_EAX(ctx, eax << 2); // SF=1
  // BPF_SET_EAX(ctx, eax << 1); // SF=2
  // SF=3
  // BPF_SET_EAX(ctx, eax >> 1); // SF=4
  return 0;
}

// 80ms RTT
// SEC("kprobe/hystart_update+0x16e")
// int BPF_KPROBE(hystart_update_0x16e) {
//   u64 ecx = BPF_ECX(ctx);
//   // BPF_SET_ECX(ctx, ecx << 1);
//   return 0;
// }

// // 80ms RTT 4000
// SEC("kprobe/hystart_update+0x15f")
// int BPF_KPROBE(hystart_update_0x15f) {
//   u64 ecx = BPF_ECX(ctx);
//   BPF_SET_ECX(ctx, ecx << 1);
//   return 0;
// }