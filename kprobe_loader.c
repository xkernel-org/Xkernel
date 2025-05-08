// SPDX-License-Identifier: GPL-2.0
#include <stdio.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include <errno.h>

#define BPF_FILE "bpf/kprobe.bpf.o"

#define KPROBE_FUNC_NAME "assign_nr_requests"
#define KRETPROBE_FUNC_NAME "read_nr_requests"

#define KPROBE_EVENT_NAME "blk_alloc_queue"

int main() {
    struct bpf_object *obj;
    struct bpf_program *prog;
    struct bpf_link *link = NULL;
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

    prog = bpf_object__find_program_by_name(obj, KPROBE_FUNC_NAME);
    if (!prog) {
        fprintf(stderr, "Failed to find program\n");
        return 1;
    }

    struct bpf_kprobe_opts opts = {};
    opts.sz = sizeof(opts);
    opts.offset = 0x1be;

    link = bpf_program__attach_kprobe_opts(prog, KPROBE_EVENT_NAME, &opts);
    if (!link) {
        fprintf(stderr, "Failed to attach kprobe\n");
        return 1;
    }

    prog = bpf_object__find_program_by_name(obj, KRETPROBE_FUNC_NAME);
    if (!prog) {
        fprintf(stderr, "Failed to find program\n");
        return 1;
    }

    link = bpf_program__attach_kprobe(prog, true, KPROBE_EVENT_NAME);
    if (!link) {
        fprintf(stderr, "Failed to attach kretprobe\n");
        return 1;
    }

    printf("Kprobe attached successfully. Check trace_pipe.\n");
    while (1) sleep(1);
}