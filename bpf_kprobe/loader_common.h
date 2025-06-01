#ifndef __LOADER_COMMON_H__
#define __LOADER_COMMON_H__

#include <bpf/libbpf.h>

namespace xkernel {

struct xkernel_prog_params {
    // BPF function name
    const char *bpf_func_name;
    // Whether the function is a kretprobe
    bool is_kretprobe;
    // Kernel function name attached to
    const char *kernel_func_name;
    // Offset of the kernel function
    int offset;
};

class XKernelLoader {
public:
    XKernelLoader(const char *bpf_file);
    ~XKernelLoader();

    void list_progs();

    int attach_prog(struct xkernel_prog_params *params);
private:
    ::bpf_object *obj_;
};

}; // namespace xkernel

#endif