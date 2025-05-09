// SPDX-License-Identifier: GPL-2.0
#include <stdio.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include <errno.h>

#define BPF_FILE "bpf/kprobe.bpf.o"

struct xkernel_prog_params {
    char *func_name;
    bool is_kretprobe;
    char *event_name;
    int offset;
};

struct xkernel_prog_params progs[] = {
    {
        .func_name = "assign_nr_requests",
        .is_kretprobe = false,
        .event_name = "blk_alloc_queue",
        .offset = 0x1be,
    },
    {
        .func_name = "read_nr_requests",
        .is_kretprobe = true,
        .event_name = "blk_alloc_queue",
    },
    {
        .func_name = "check_MAX_SCHED_RQ",
        .is_kretprobe = false,
        .event_name = "blk_mq_tag_update_depth",
        .offset = 0x34,
    },
    {
        .func_name = "cont_check_MAX_SCHED_RQ",
        .is_kretprobe = false,
        .event_name = "blk_mq_tag_update_depth",
        .offset = 0x3c,
    },
    {
        .func_name = "jump_check_MAX_SCHED_RQ",
        .is_kretprobe = false,
        .event_name = "blk_mq_tag_update_depth",
        .offset = 0xa1,
    },
};

static int attach_prog(struct bpf_object *obj, struct xkernel_prog_params *params) {
    struct bpf_program *prog;
    struct bpf_link *link = NULL;

    prog = bpf_object__find_program_by_name(obj, params->func_name);
    if (!prog) {
        fprintf(stderr, "Failed to find program\n");
        return -1;
    }

    if (params->is_kretprobe) {
        link = bpf_program__attach_kprobe(prog, true, params->event_name);
    } else {
        struct bpf_kprobe_opts opts = {};
        opts.sz = sizeof(opts);
        opts.offset = params->offset;
        link = bpf_program__attach_kprobe_opts(prog, params->event_name, &opts);
    }

    if (!link) {
        fprintf(stderr, "Failed to attach kprobe\n");
        return -1;
    }

    if (params->is_kretprobe) {
        printf("Attached [%s] to <kretprobe> of <%s>\n", params->func_name, params->event_name);
    } else {
        printf("Attached [%s] to <krpobe> of <%s> with offset <%d>\n", params->func_name, params->event_name, params->offset);
    }

    return 0;
}

int main() {
    struct bpf_object *obj;

    int err;

    obj = bpf_object__open_file(BPF_FILE, NULL);
    if (libbpf_get_error(obj)) {
        fprintf(stderr, "Failed to open BPF object\n");
        return 1;
    }

    err = bpf_object__load(obj);
    if (err) {
        fprintf(stderr, "Failed to load BPF object: %s\n", strerror(-err));
        return 1;
    }

    for (int i = 0; i < sizeof(progs) / sizeof(progs[0]); i++) {
        if (attach_prog(obj, &progs[i]) < 0) {
            fprintf(stderr, "Failed to attach program\n");
            return 1;
        }
    }

    printf("Kprobe attached successfully. Check /sys/kernel/tracing/trace_pipe.\n");
    while (1) sleep(1);
}