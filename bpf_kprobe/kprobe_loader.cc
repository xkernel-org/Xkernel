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
        .bpf_func_name = "hystart_update_0xcc",
        .is_kretprobe = false,
        .kernel_func_name = "hystart_update",
        .offset = 0xcc,
    },
    {
        .bpf_func_name = "hystart_update_0xd9",
        .is_kretprobe = false,
        .kernel_func_name = "hystart_update",
        .offset = 0xd9,
    },
    {
        .bpf_func_name = "hystart_update",
        .is_kretprobe = false,
        .kernel_func_name = "hystart_update",
        .offset = 0,
    }
};

int main() {
    XKernelLoader loader(BPF_FILE);

    for (size_t i = 0; i < sizeof(progs) / sizeof(progs[0]); i++) {
        if (loader.attach_prog(&progs[i]) < 0) {
            fprintf(stderr, "Failed to attach program\n");
            return 1;
        }
    }

    printf("Kprobe attached successfully. Check /sys/kernel/tracing/trace_pipe\n");
    while (1) sleep(1);
}