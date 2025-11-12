// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_endian.h>

#include "xkernel.bpf.h"

SEC("kprobe/tcp_rack_detect_loss+0x6a")
int BPF_KPROBE(tcp_rack_detect_loss_6a, struct sock *sk) {

  bpf_printk("sk: %p\n", sk);
  if (!transition_done(ctx)) {
    return 0;
  }
  bpf_printk("1-sk: %p\n", sk);

  u64 r15d = BPF_R15(ctx);
  BPF_SET_R15(ctx, r15d << 1);
  return 0;
}

// SEC("kprobe/dev_gro_receive")
// int BPF_KPROBE(dev_gro_receive, struct napi_struct *napi, struct sk_buff *skb) {
//   bpf_printk("dev_gro_receive: napi: %p, skb: %p\n", napi, skb);
//   u32 skb_len;
//   if (bpf_probe_read_kernel(&skb_len, sizeof(skb_len), &skb->len) != 0) {
//     return 0;
//   }
//   bpf_printk("skb_len: %u\n", skb_len);
//   return 0;
// }

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

SEC("kprobe/tcp_sendmsg")
int BPF_KPROBE(tcp_sendmsg, struct sock *sk) {
  struct sock_common *skc = (struct sock_common *)sk;
  struct tcp_sock *tcp_sk = tcp_sk(sk);
  struct bictcp *ca = inet_csk_ca(sk);
  u32 ipv4_daddr;
  u32 ipv4_saddr;
  u16 family;
  u16 sport;
  if (bpf_probe_read_kernel(&family, sizeof(family), &skc->skc_family) != 0) {
    return 0;
  }
  if (bpf_probe_read_kernel(&sport, sizeof(sport), &skc->skc_num) != 0) {
    return 0;
  }
  bpf_printk("source port : %u", bpf_ntohs(sport));

  struct minmax m;
  if (bpf_probe_read_kernel(&m, sizeof(m), &tcp_sk->rtt_min) != 0) {
    return 0;
  }
  u32 rtt_min_us;
  if (bpf_probe_read_kernel(&rtt_min_us, sizeof(rtt_min_us), &m.s[0].v) != 0) {
    return 0;
  } 
  bpf_printk("rtt_min: %u\n", rtt_min_us);
  u32 delay_min;
  if (bpf_probe_read_kernel(&delay_min, sizeof(delay_min), &ca->delay_min) != 0) {
    return 0;
  }
  bpf_printk("delay_min: %u\n", delay_min);

  if (bpf_probe_read_kernel(&ipv4_daddr, sizeof(ipv4_daddr), &skc->skc_daddr) != 0) {
    return 0;
  }
  if (bpf_probe_read_kernel(&ipv4_saddr, sizeof(ipv4_saddr), &skc->skc_rcv_saddr) != 0) {
    return 0;
  }
  bpf_printk("tcp_sendmsg: sk: %p, ipv4_daddr: %u.%u.%u.%u, ipv4_saddr: %u.%u.%u.%u\n", sk, ipv4_daddr >> 24, (ipv4_daddr >> 16) & 0xFF, (ipv4_daddr >> 8) & 0xFF, ipv4_daddr & 0xFF, ipv4_saddr >> 24, (ipv4_saddr >> 16) & 0xFF, (ipv4_saddr >> 8) & 0xFF, ipv4_saddr & 0xFF);
  return 0;
}