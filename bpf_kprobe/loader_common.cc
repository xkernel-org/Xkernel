#include "loader_common.h"

#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <linux/bpf.h>
#include <unistd.h>
#include <cassert>
#include <cstdlib>
#include <string>
#include <mutex>
#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <algorithm>
#include <filesystem>
#include <sys/stat.h>
#include <sys/types.h>
#include <cerrno>
#include <cstring>

namespace xkernel {

static uint32_t prog_cnt = 0;

XKernelLoader::XKernelLoader(const char *bpf_file, bool pin): pin_(pin) {
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

XKernelLoader::~XKernelLoader() { 
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

// ==========================================
// 补全缺失的 BPF 指令宏 (兼容 C/C++)
// ==========================================

#ifndef BPF_MOV64_IMM
#define BPF_MOV64_IMM(DST, IMM) \
    ((struct bpf_insn) { \
        .code  = BPF_ALU64 | BPF_MOV | BPF_K, \
        .dst_reg = DST, \
        .src_reg = 0, \
        .off   = 0, \
        .imm   = (int)(IMM) })
#endif

#ifndef BPF_MOV64_REG
#define BPF_MOV64_REG(DST, SRC) \
    ((struct bpf_insn) { \
        .code  = BPF_ALU64 | BPF_MOV | BPF_X, \
        .dst_reg = DST, \
        .src_reg = SRC, \
        .off   = 0, \
        .imm   = 0 })
#endif

#ifndef BPF_ALU64_IMM
#define BPF_ALU64_IMM(OP, DST, IMM) \
    ((struct bpf_insn) { \
        .code  = BPF_ALU64 | OP | BPF_K, \
        .dst_reg = DST, \
        .src_reg = 0, \
        .off   = 0, \
        .imm   = IMM })
#endif

#ifndef BPF_STX_MEM
#define BPF_STX_MEM(SIZE, DST, SRC, OFF) \
    ((struct bpf_insn) { \
        .code  = BPF_STX | BPF_MEM | SIZE, \
        .dst_reg = DST, \
        .src_reg = SRC, \
        .off   = OFF, \
        .imm   = 0 })
#endif

#ifndef BPF_EMIT_CALL
#define BPF_EMIT_CALL(FUNC) \
    ((struct bpf_insn) { \
        .code  = BPF_JMP | BPF_CALL, \
        .dst_reg = 0, \
        .src_reg = 0, \
        .off   = 0, \
        .imm   = (FUNC) })
#endif

#ifndef BPF_EXIT_INSN
#define BPF_EXIT_INSN() \
    ((struct bpf_insn) { \
        .code  = BPF_JMP | BPF_EXIT, \
        .dst_reg = 0, \
        .src_reg = 0, \
        .off   = 0, \
        .imm   = 0 })
#endif

long run_bpf_ktime_printer(int repeat) {
  // 构造字符串 "%llu\0" 的十六进制 (小端序): 0x00756C6C25
  struct bpf_insn insns[] = {
      BPF_EMIT_CALL(BPF_FUNC_ktime_get_ns),           // R0 = time
      BPF_MOV64_REG(BPF_REG_3, BPF_REG_0),            // R3 = time (printk 参数3)
      BPF_MOV64_IMM(BPF_REG_1, 0x00756C6C25ULL),      // R1 = "%llu\0"
      BPF_STX_MEM(BPF_DW, BPF_REG_10, BPF_REG_1, -8), // 压栈 [FP-8]
      BPF_MOV64_REG(BPF_REG_1, BPF_REG_10),           // R1 = FP
      BPF_ALU64_IMM(BPF_ADD, BPF_REG_1, -8),          // R1 = FP-8 (fmt)
      BPF_MOV64_IMM(BPF_REG_2, 5),                    // R2 = 5 (len)
      BPF_EMIT_CALL(BPF_FUNC_trace_printk),           // call trace_printk
      BPF_MOV64_IMM(BPF_REG_0, 0),                    // return 0
      BPF_EXIT_INSN(),
  };

  // 1. 加载 (SOCKET_FILTER 模式加载最快且无副作用)
  // 注意：C++ 中 sizeof(insns) 计算正常
  int prog_fd = bpf_prog_load(BPF_PROG_TYPE_SOCKET_FILTER, NULL, "GPL",
                              insns, sizeof(insns)/sizeof(struct bpf_insn), NULL);
  if (prog_fd < 0) return -1;

  // 2. 执行 (test_run_opts)
  char data[14] = {0}; // 伪造 dummy 数据
  struct bpf_test_run_opts opts = {}; // C++ 零初始化
  opts.sz = sizeof(opts);
  opts.data_in = data;
  opts.data_size_in = sizeof(data);
  opts.repeat = repeat; // 关键：内核内循环
  
  int err = bpf_prog_test_run_opts(prog_fd, &opts);
  
  // 保存 errno 并在关闭 fd 前处理，防止 close 覆盖 errno（虽然此处只关心 test_run 的返回值）
  close(prog_fd); 

  return err ? -1 : (long)(opts.duration / (repeat ? repeat : 1));
}

int XKernelLoader::attach_all_progs() {
  struct ::bpf_program *prog;
  int ret = 0;

  run_bpf_ktime_printer(1);

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

  run_bpf_ktime_printer(1);

  return 0;
}

int generate_cs_artifact_bpf_header(const char *cs_path, const char *output_path) {
  std::ifstream cs_file(cs_path);
  if (!cs_file.is_open()) {
    fprintf(stderr, "Failed to open cs_file: %s\n", cs_path);
    return -1;
  }
  
  // The format looks like this (one per line, split by comma)
  // function_name,function_address,soff,eoff
  // e.g., vm_mmap_pgoff,0xffffffff98299640,0x6,0x161

  std::vector<std::pair<std::string, __u32>> cs_info_list; // Store function_name and soff for BPF generation
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
    // Parse soff, handling both "0x0" and "0" formats
    __u32 soff;
    if (soff_str.substr(0, 2) == "0x" || soff_str.substr(0, 2) == "0X") {
      soff = std::stoul(soff_str, nullptr, 16);
    } else {
      soff = std::stoul(soff_str, nullptr, 16);
    }
    cs_info_list.push_back({function_name, soff});
  }

  // Ensure output directory exists
  std::filesystem::path output_file_path(output_path);
  std::filesystem::path output_dir = output_file_path.parent_path();
  if (!output_dir.empty() && !std::filesystem::exists(output_dir)) {
    fprintf(stderr, "Creating output directory: %s\n", output_dir.c_str());
    if (!std::filesystem::create_directories(output_dir)) {
      fprintf(stderr, "Failed to create output directory: %s\n", output_dir.c_str());
      return -1;
    }
  }
  
  fprintf(stderr, "Generating BPF header file: %s\n", output_path);

  // Remove old file if exists to ensure fresh generation
  if (std::filesystem::exists(output_path)) {
    std::filesystem::remove(output_path);
  }

  std::ofstream bpf_header(output_path, std::ios::out | std::ios::trunc);
  if (!bpf_header.is_open()) {
    fprintf(stderr, "Failed to create %s: %s\n", output_path, strerror(errno));
    return -1;
  }

  bpf_header << "#ifndef __CS_ARTIFACT_BPF_H__\n";
  bpf_header << "#define __CS_ARTIFACT_BPF_H__\n\n";
  bpf_header << "#include <bpf/bpf_helpers.h>\n";
  bpf_header << "#include <bpf/bpf_tracing.h>\n\n";
  bpf_header << "#include \"xkernel.bpf.h\"\n\n";

  for (size_t i = 0; i < cs_info_list.size(); i++) {
    const std::string& function_name = cs_info_list[i].first;
    __u32 soff = cs_info_list[i].second;
    
    std::string sec_name;
    std::string bpf_func_name;
    
    if (soff == 0) {
      // If soff is 0, don't add +0x0 suffix
      sec_name = "kprobe/" + function_name;
      bpf_func_name = function_name;
    } else {
      // Format soff as hex string (e.g., 0x6 -> "0x6", 0x161 -> "0x161")
      std::ostringstream soff_hex;
      soff_hex << "0x" << std::hex << soff;
      std::string soff_str = soff_hex.str();
      
      // Generate function name: function_name_soff (e.g., vm_mmap_pgoff_6)
      // Remove "0x" prefix for function name
      std::string func_name_suffix = soff_str;
      if (func_name_suffix.substr(0, 2) == "0x") {
        func_name_suffix = func_name_suffix.substr(2);
      }
      bpf_func_name = function_name + "_" + func_name_suffix;
      
      // Generate SEC name: kprobe/function_name+soff (e.g., kprobe/vm_mmap_pgoff+0x6)
      sec_name = "kprobe/" + function_name + "+" + soff_str;
    }
    
    bpf_header << "SEC(\"" << sec_name << "\")\n";
    bpf_header << "int BPF_KPROBE(" << bpf_func_name << ") {\n";
    bpf_header << "    per_task_transition_handler(ctx);\n";
    bpf_header << "    return 0;\n";
    bpf_header << "}\n\n";
  }

  bpf_header << "#endif\n";
  
  // Ensure all data is written
  bpf_header.flush();
  if (bpf_header.fail()) {
    fprintf(stderr, "Error: Failed to write to %s\n", output_path);
    bpf_header.close();
    return -1;
  }
  
  bpf_header.close();
  
  // Verify file was created and has content
  if (!std::filesystem::exists(output_path)) {
    fprintf(stderr, "Error: File %s was not created\n", output_path);
    return -1;
  }
  
  auto file_size = std::filesystem::file_size(output_path);
  if (file_size == 0) {
    fprintf(stderr, "Error: File %s is empty\n", output_path);
    return -1;
  }
  
  fprintf(stderr, "Successfully generated %s (%zu bytes, %zu entries)\n", 
          output_path, file_size, cs_info_list.size());

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