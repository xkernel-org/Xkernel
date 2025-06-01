#include "loader_common.h"

#include <bpf/libbpf.h>
#include <cstdlib>

namespace xkernel {

XKernelLoader::XKernelLoader(const char *bpf_file)
{
    obj_ = ::bpf_object__open_file(bpf_file, NULL);
    if (::libbpf_get_error(obj_)) {
        fprintf(stderr, "Failed to open bpf object\n");
        exit(1);
    }

    int err = ::bpf_object__load(obj_);
    if (err) {
        fprintf(stderr, "Failed to load bpf object: %s\n", strerror(-err));
        exit(1);
    }
}

XKernelLoader::~XKernelLoader()
{
    ::bpf_object__close(obj_);
}

int XKernelLoader::attach_prog(struct xkernel_prog_params *params) 
{
    struct ::bpf_program *prog;
    struct ::bpf_link *link = NULL;

    prog = ::bpf_object__find_program_by_name(obj_, params->bpf_func_name);
    if (!prog) {
        fprintf(stderr, "Failed to find program\n");
        return -1;
    }

    if (params->is_kretprobe) {
        link = ::bpf_program__attach_kprobe(prog, true, params->kernel_func_name);
    } else {
        struct ::bpf_kprobe_opts opts = {};
        opts.sz = sizeof(opts);
        opts.offset = params->offset;
        link = ::bpf_program__attach_kprobe_opts(prog, params->kernel_func_name, &opts);
    }

    if (!link) {
        fprintf(stderr, "Failed to attach kprobe\n");
        return -1;
    }

    if (params->is_kretprobe) {
        printf("Attached [%s] to <kretprobe> of <%s>\n", params->bpf_func_name, params->kernel_func_name);
    } else {
        printf("Attached [%s] to <krpobe> of <%s> with offset <%d>\n", params->bpf_func_name, params->kernel_func_name, params->offset);
    }

    return 0;
}

}; // namespace xkernel