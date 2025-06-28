#include "loader_common.h"

#include <bpf/libbpf.h>
#include <cassert>
#include <cstdlib>
#include <string>

namespace xkernel {

static uint32_t prog_cnt = 0;

XKernelLoader::XKernelLoader(const char *bpf_file) {
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

XKernelLoader::~XKernelLoader() { ::bpf_object__close(obj_); }

int XKernelLoader::attach_kretprobe(struct ::bpf_program *prog,
                                    const char *kernel_func_name) {
  auto link = ::bpf_program__attach_kprobe(prog, true, kernel_func_name);
  if (!link) {
    fprintf(stderr, "Failed to attach kprobe\n");
    return -1;
  }
  return 0;
}

int XKernelLoader::attach_kprobe(struct ::bpf_program *prog,
                                 const char *kernel_func_name, size_t offset) {
  struct ::bpf_kprobe_opts opts = {
      .sz = sizeof(opts),
      .offset = offset,
  };
  auto link = ::bpf_program__attach_kprobe_opts(prog, kernel_func_name, &opts);

  if (!link) {
    fprintf(stderr, "Failed to attach kprobe\n");
    return -1;
  }
  return 0;
}

int XKernelLoader::attach_all_progs() {
  struct ::bpf_program *prog;
  int ret = 0;

  bpf_object__for_each_program(prog, obj_) {
    const char *bpf_func_name = bpf_program__name(prog);
    const char *bpf_sec_name = bpf_program__section_name(prog);

    auto sec_str = std::string(bpf_sec_name);

    auto pos = sec_str.find('/');
    assert(pos != std::string::npos);

    auto kprobe_type = sec_str.substr(0, pos);
    assert(kprobe_type == "kprobe" || kprobe_type == "kretprobe");

    auto function_name_str = sec_str.substr(pos + 1);
    assert(!function_name_str.empty());

    if (kprobe_type == "kretprobe") {
      printf("[%d]\n\tBPF func:\t%s\n\ttype:\t\t%s\n\tkernel func:\t%s\n",
             ++prog_cnt, bpf_func_name, kprobe_type.c_str(),
             function_name_str.c_str());
      ret = attach_kretprobe(prog, function_name_str.c_str());
    } else {
      pos = function_name_str.find('+');

      auto offset = std::stoul("0", nullptr, 16);
      auto function_name = function_name_str;

      if (pos != std::string::npos) {
        function_name = function_name_str.substr(0, pos);
        auto offset_str = function_name_str.substr(pos + 1);
        offset = std::stoul(offset_str, nullptr, 16);
      }
      printf("[%d]\n\tBPF func:\t%s\n\ttype:\t\t%s\n\tkernel "
             "func:\t%s\n\toffset:\t\t0x%lx\n",
             ++prog_cnt, bpf_func_name, kprobe_type.c_str(),
             function_name.c_str(), offset);
      ret = attach_kprobe(prog, function_name.c_str(), offset);
    }
    if (ret)
      return ret;
  }

  return 0;
}

}; // namespace xkernel