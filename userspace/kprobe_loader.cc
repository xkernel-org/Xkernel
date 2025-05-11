// SPDX-License-Identifier: GPL-2.0
#include <stdio.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include <errno.h>

#include "loader_common.h"

using namespace xkernel;

#define BPF_FILE "bpf/kprobe.bpf.o"

struct xkernel_prog_params progs[] = {
    {
        .bpf_func_name = "assign_nr_requests",
        .is_kretprobe = false,
        .kernel_func_name = "blk_alloc_queue",
        .offset = 0x1be,
    },
    {
        .bpf_func_name = "read_nr_requests",
        .is_kretprobe = true,
        .kernel_func_name = "blk_alloc_queue",
    },
    {
        .bpf_func_name = "check_MAX_SCHED_RQ",
        .is_kretprobe = false,
        .kernel_func_name = "blk_mq_tag_update_depth",
        .offset = 0x34,
    },
    {
        .bpf_func_name = "cont_check_MAX_SCHED_RQ",
        .is_kretprobe = false,
        .kernel_func_name = "blk_mq_tag_update_depth",
        .offset = 0x3c,
    },
    {
        .bpf_func_name = "jump_check_MAX_SCHED_RQ",
        .is_kretprobe = false,
        .kernel_func_name = "blk_mq_tag_update_depth",
        .offset = 0xa1,
    },
    {
        .bpf_func_name = "xkernel_test_func1_0x5e",
        .is_kretprobe = false,
        .kernel_func_name = "xkernel_test_func1",
        .offset = 0x5e,
    },
    {
        .bpf_func_name = "xkernel_test_func1_0x91",
        .is_kretprobe = false,
        .kernel_func_name = "xkernel_test_func1",
        .offset = 0x91,
    },
    {
        .bpf_func_name = "xkernel_test_func1_0x63",
        .is_kretprobe = false,
        .kernel_func_name = "xkernel_test_func1",
        .offset = 0x63,
    },
};

int main() {
    XKernelLoader loader(BPF_FILE);

    for (size_t i = 0; i < sizeof(progs) / sizeof(progs[0]); i++) {
        if (loader.attach_prog(&progs[i]) < 0) {
            fprintf(stderr, "Failed to attach program\n");
            return 1;
        }
    }

    printf("Kprobe attached successfully. Check /sys/kernel/tracing/trace_pipe.\n");
    while (1) sleep(1);
}