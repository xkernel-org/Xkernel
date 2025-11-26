// SPDX-License-Identifier: GPL-2.0

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_endian.h>

#include "xkernel.bpf.h"

struct {
  __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
  __uint(max_entries, 1);
  __type(key, __u32);
  __type(value, __u64);
} wait_ts_map SEC(".maps");

struct {
  __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
  __uint(max_entries, 1);
  __type(key, __u32);
  __type(value, __u64);
} send_ts_map SEC(".maps");

SEC("kprobe/tcp_sendmsg_locked+0x3be")
int BPF_KPROBE(tcp_sendmsg_locked_0x3be) {
  if (!transition_done(ctx)) {
    return 0;
  }
  bpf_printk("tcp_sendmsg_locked_0x3be\n");
  return 0;
}

SEC("kprobe/tcp_sendmsg_locked")
int BPF_KPROBE(tcp_sendmsg_locked) {
  struct task_struct *task = bpf_get_current_task_btf();
  if (bpf_strncmp(task->comm, TASK_COMM_LEN, "iperf3") == 0) {
    __u32 key = 0;
    __u64 *t1 = bpf_map_lookup_elem(&send_ts_map, &key);
    if (t1 == NULL) {
      return 0;
    }
    *t1 = bpf_ktime_get_ns();
  }
  return 0;
}

SEC("kretprobe/tcp_sendmsg_locked")
int BPF_KRETPROBE(tcp_sendmsg_locked_ret) {
  struct task_struct *task = bpf_get_current_task_btf();
  if (bpf_strncmp(task->comm, TASK_COMM_LEN, "iperf3") == 0) {
    __u32 key = 0;
    __u64 *t1 = bpf_map_lookup_elem(&send_ts_map, &key);
    if (t1 == NULL) {
      return 0;
    }

    LOG_CPU("tcp_sendmsg_locked: %lld us", (bpf_ktime_get_ns() - *t1) / 1000);
  }
  return 0;
}

SEC("kprobe/sk_stream_wait_memory")
int BPF_KPROBE(sk_stream_wait_memory) {
  struct task_struct *task = bpf_get_current_task_btf();
  if (bpf_strncmp(task->comm, TASK_COMM_LEN, "iperf3") == 0) {
    __u32 key = 0;
    __u64 *t1 = bpf_map_lookup_elem(&wait_ts_map, &key);
    if (t1 == NULL) {
      return 0;
    }
    *t1 = bpf_ktime_get_ns();
  }
  return 0;
}

SEC("kretprobe/sk_stream_wait_memory")
int BPF_KRETPROBE(sk_stream_wait_memory_ret) {
  struct task_struct *task = bpf_get_current_task_btf();
  if (bpf_strncmp(task->comm, TASK_COMM_LEN, "iperf3") == 0) {
    __u32 key = 0;
    __u64 *t1 = bpf_map_lookup_elem(&wait_ts_map, &key);
    if (t1 == NULL) {
      return 0;
    }
    LOG_CPU("sk_stream_wait_memory: %lld us", (bpf_ktime_get_ns() - *t1) / 1000);
  }
  return 0;
}
