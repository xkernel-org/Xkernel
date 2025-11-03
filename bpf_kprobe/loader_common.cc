#include "loader_common.h"

#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <unistd.h>
#include <cassert>
#include <cstdlib>
#include <string>
#include <mutex>
#include <string>
#include <fstream>
#include <sstream>
#include <vector>
#include <algorithm>

namespace xkernel {

static uint32_t prog_cnt = 0;

XKernelLoader::XKernelLoader(const char *bpf_file, bool one_shot, bool pin): one_shot_(one_shot), pin_(pin) {
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

int XKernelLoader::detach_all_progs_one_shot() {
  struct ::bpf_program *prog;
  bpf_object__for_each_program(prog, obj_) {
    auto prog_fd = bpf_program__fd(prog);
    auto bpf_func_name = bpf_program__name(prog);

    if (strncmp(bpf_func_name, "oneshot_exit_", 13) != 0) {
      continue;
    }

    struct bpf_test_run_opts opts = {};
    opts.sz = sizeof(opts);
    int err = bpf_prog_test_run_opts(prog_fd, &opts);
    if (err) {
      fprintf(stderr, "Failed to run program: %s\n", strerror(-err));
      return -1;
    }

    printf("%s returned %d\n", bpf_program__name(prog), opts.retval);
  }
  return 0;
}

XKernelLoader::~XKernelLoader() { 
  if (one_shot_) {
    detach_all_progs_one_shot();
  }
  ::bpf_object__close(obj_);
}

int XKernelLoader::attach_kretprobe(struct ::bpf_program *prog,
                                    const char *kernel_func_name, std::string pin_path) {
  auto link = ::bpf_program__attach_kprobe(prog, true, kernel_func_name);
  if (!link) {
    fprintf(stderr, "Failed to attach kprobe\n");
    return -1;
  }

  if (pin_) {
    auto err = ::bpf_link__pin(link, pin_path.c_str());
    if (err) {
      fprintf(stderr, "Failed to pin bpf link: %s\n", strerror(-err));
      return -1;
    }
  }

  return 0;
}

int XKernelLoader::attach_kprobe(struct ::bpf_program *prog,
                                 const char *kernel_func_name, size_t offset, std::string pin_path) {
  struct ::bpf_kprobe_opts opts = {
      .sz = sizeof(opts),
      .offset = offset,
  };
  auto link = ::bpf_program__attach_kprobe_opts(prog, kernel_func_name, &opts);

  if (!link) {
    fprintf(stderr, "Failed to attach kprobe\n");
    return -1;
  }

  if (pin_) {
    auto err = ::bpf_link__pin(link, pin_path.c_str());
    if (err) {
      fprintf(stderr, "Failed to pin bpf link: %s\n", strerror(-err));
      return -1;
    }
  }

  return 0;
}

int XKernelLoader::attach_all_progs_one_shot() {
  struct ::bpf_program *prog;
  bpf_object__for_each_program(prog, obj_) {
    auto prog_fd = bpf_program__fd(prog);
    auto bpf_func_name = bpf_program__name(prog);

    if (strncmp(bpf_func_name, "oneshot_init_", 13) != 0) {
      continue;
    }

    struct bpf_test_run_opts opts = {};
    opts.sz = sizeof(opts);
    int err = bpf_prog_test_run_opts(prog_fd, &opts);
    if (err) {
      fprintf(stderr, "Failed to run program: %s\n", strerror(-err));
      return -1;
    }

    printf("%s returned %d\n", bpf_program__name(prog), opts.retval);
  }
  return 0;
}

int XKernelLoader::attach_all_progs() {
  struct ::bpf_program *prog;
  int ret = 0;

  bpf_object__for_each_program(prog, obj_) {
    const char *bpf_func_name = bpf_program__name(prog);
    const char *bpf_sec_name = bpf_program__section_name(prog);

    std::string pin_path = "/sys/fs/bpf/xkernel/" + std::string(bpf_func_name);

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
      ret = attach_kretprobe(prog, function_name_str.c_str(), pin_path);
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
      ret = attach_kprobe(prog, function_name.c_str(), offset, pin_path);
    }
    if (ret)
      return ret;
  }
  return 0;
}

int XKernelLoader::load_cricial_spans(const char *cs_path) {
  auto cs_map = bpf_object__find_map_by_name(obj_, "cs_map");
  if (!cs_map) {
    fprintf(stderr, "Failed to find cs_map\n");
    return -1;
  }
  auto cs_map_fd = bpf_map__fd(cs_map);
  if (cs_map_fd < 0) {
    fprintf(stderr, "Failed to get cs_map fd\n");
    return -1;
  }
  auto cs_len_map = bpf_object__find_map_by_name(obj_, ".bss.cs_len");
  if (!cs_len_map) {
    fprintf(stderr, "Failed to find .bss.cs_len\n");
    return -1;
  }
  auto cs_len_fd = bpf_map__fd(cs_len_map);
  if (cs_len_fd < 0) {
    fprintf(stderr, "Failed to get .bss.cs_len fd\n");
    return -1;
  }

  std::ifstream cs_file(cs_path);
  if (!cs_file.is_open()) {
    fprintf(stderr, "Failed to open cs_file\n");
    return -1;
  }
  
  // The format looks like this (one per line, split by comma)
  // function_name,function_address,soff,eoff
  // e.g., vm_mmap_pgoff,0xffffffff98299640,0x6,0x161

  std::vector<critical_span> cs_list;
  std::string line;
  while (std::getline(cs_file, line)) {
    std::istringstream iss(line);
    std::string function_name, function_address_str, soff_str, eoff_str;
    std::getline(iss, function_name, ',');
    std::getline(iss, function_address_str, ',');
    std::getline(iss, soff_str, ',');
    std::getline(iss, eoff_str, ',');
    if (function_name.empty() || function_address_str.empty() || soff_str.empty() || eoff_str.empty()) {
      fprintf(stderr, "Malformed line in %s: %s\n", cs_path, line.c_str());
      continue;
    }
    __u64 function_address = std::stoull(function_address_str, nullptr, 16);
    __u32 soff = std::stoul(soff_str, nullptr, 16);
    __u32 eoff = std::stoul(eoff_str, nullptr, 16);
    cs_list.push_back({
      .soff = function_address + soff,
      .eoff = function_address + eoff,
    });
  }

  std::sort(cs_list.begin(), cs_list.end(), [](const critical_span &a, const critical_span &b) {
    if (a.soff != b.soff) return a.soff < b.soff;
    return a.eoff > b.eoff;
  });

  auto cs_len = cs_list.size();
  __u32 key = 0;
  if (bpf_map_update_elem(cs_len_fd, &key, &cs_len, BPF_ANY)) {
    fprintf(stderr, "Failed to update cs_len\n");
    return -1;
  }

  for (size_t i = 0; i < cs_list.size(); i++) {
    if (bpf_map_update_elem(cs_map_fd, &i, &cs_list[i], BPF_ANY)) {
      fprintf(stderr, "Failed to update cs_map\n");
      return -1;
    }
  }

  return 0;
}

void XKernelLoader::print_stack_trace(uint32_t stack_id) {
  uint64_t stack_trace[MAX_STACK_DEPTH] = {};
  bpf_map_lookup_elem(stack_trace_map_fd_, &stack_id, &stack_trace);

  // Find the first and last valid address in the stack trace
  int first = -1, last = -1;
  for (int i = 0; i < MAX_STACK_DEPTH && stack_trace[i] != 0; i++) {
    if (first == -1) first = i;
    last = i;
  }
  printf("[stack_id: %d]\n", stack_id);
  for (int i = 0; i <= last && i < MAX_STACK_DEPTH; i++) {
    printf("stack[%d] = %lx\n", i, stack_trace[i]);
  }

  printf("Use the following command to dump assembly:\n");
  printf("sudo objdump -d --start-address=0xxxxxxx --stop-address=0xxxxxxx /proc/kcore\n");
}

int XKernelLoader::dump_stack_trace() {
  
  static std::once_flag once_flag_;
  std::call_once(once_flag_, [this]() {
    auto count_map = bpf_object__find_map_by_name(obj_, "stack_count_map");
    auto stack_trace_map = bpf_object__find_map_by_name(obj_, "stack_trace_map");
    if (!count_map || !stack_trace_map) {
      printf("No stack count or stack trace map found\n");
      return -1;
    }
  
    count_map_fd_ = bpf_map__fd(count_map);
    stack_trace_map_fd_ = bpf_map__fd(stack_trace_map);
    return 0;
  });

  int bss_map_fd = bpf_object__find_map_fd_by_name(obj_, ".bss.call_store_stack");
  if (bss_map_fd < 0) {
      fprintf(stderr, "Failed to find .bss map\n");
      return -1;
  }

  uint32_t key = 0;
  uint32_t value = 0;
  if (bpf_map_lookup_elem(bss_map_fd, &key, &value) != 0) {
    fprintf(stderr, "Failed to find .bss map\n");
    return -1;
  }

  if (!count_map_fd_ || !stack_trace_map_fd_ || !value) {
    return -1;
  }

  uint32_t lookup_key = -1, next_key = 0;
  uint64_t stack_count = 0;
  while (bpf_map_get_next_key(count_map_fd_, &lookup_key, &next_key) == 0) {
    bpf_map_lookup_elem(count_map_fd_, &next_key, &stack_count);
    if (print_stack_trace_map_[next_key]) continue;
    print_stack_trace_map_[next_key] = true;
    print_stack_trace(next_key);
    lookup_key = next_key;
  }

  return 0;
}

}; // namespace xkernel