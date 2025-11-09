#ifndef __LOADER_COMMON_H__
#define __LOADER_COMMON_H__

#include <bpf/libbpf.h>

#include <unordered_map>
#include <string>

#define MAX_STACK_ENTRIES 1024
#define MAX_STACK_DEPTH 127

namespace xkernel {

struct critical_span {
  __u64 soff;
  __u64 eoff;
};

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
  XKernelLoader(const char *bpf_file, bool pin);
  ~XKernelLoader();

  void list_progs();

  int attach_all_progs();

  int load_cricial_spans(const char *cs_path);

  int dump_stack_trace();

private:
  ::bpf_object *obj_;

  bool pin_;

  int count_map_fd_ = 0;
  int stack_trace_map_fd_ = 0;

  std::unordered_map<uint32_t, bool> print_stack_trace_map_;

  int attach_kretprobe(struct ::bpf_program *prog,
                       const char *kernel_func_name, std::string pin_path);
  int attach_kprobe(struct ::bpf_program *prog, const char *kernel_func_name,
                    size_t offset, std::string pin_path);
                    
  void print_stack_trace(uint32_t stack_id);
};

}; // namespace xkernel

#endif