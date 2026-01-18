// SPDX-License-Identifier: GPL-2.0
#include <bpf/libbpf.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <fcntl.h>
#include <dirent.h>
#include <gflags/gflags.h>
#include <sys/socket.h>
#include <linux/netlink.h>

#include <sstream>
#include <string>
#include <vector>
#include <chrono>
#include <filesystem>
#include <cstdlib>
#include <fstream>

#include "loader_common.h"

using namespace xkernel;

DEFINE_string(files, "", "BPF files to load, separated by comma");
DEFINE_bool(quiet, false, "Quiet mode, do not print any output");
DEFINE_bool(pin, false, "Pin the BPF objects to the file system");

std::vector<XKernelLoader *> loaders;

int main(int argc, char *argv[]) {
  gflags::ParseCommandLineFlags(&argc, &argv, true);

  signal(SIGINT, [](int) {
    for (auto loader : loaders) {
      delete loader;
    }
    exit(0);
  });

  if (FLAGS_files.empty()) {
    fprintf(stderr, "files is not set\n");
    return 1;
  }

  std::vector<std::string> files;
  std::string file;
  std::istringstream ss(FLAGS_files);
  while (std::getline(ss, file, ',')) {
    if (!file.empty()) {
      if (!std::filesystem::exists(file)) {
        fprintf(stderr, "File %s does not exist\n", file.c_str());
        return 1;
      }
      files.push_back(file);
    }
  }

  // Generate cs_artifact.bpf.h before creating XKernelLoader
  const char *cs_path = "/dev/shm/xkernel/cs";
  
  // Use absolute path for output file
  std::filesystem::path current_path = std::filesystem::current_path();
  std::string bpf_header_path = (current_path / "bpf_kprobe/bpf" / "cs_artifact.bpf.h").string();
  
  fprintf(stderr, "Current working directory: %s\n", current_path.c_str());
  fprintf(stderr, "Output BPF header path: %s\n", bpf_header_path.c_str());
  
  // Check if cs_path exists and is not empty
  bool cs_file_valid = false;
  if (std::filesystem::exists(cs_path)) {
    std::ifstream cs_file(cs_path);
    if (cs_file.is_open()) {
      std::string line;
      if (std::getline(cs_file, line)) {
        // Check if line is not empty (after trimming whitespace)
        if (!line.empty() && line.find_first_not_of(" \t\n\r") != std::string::npos) {
          cs_file_valid = true;
        }
      }
      cs_file.close();
    }
  }
  
  if (cs_file_valid) {
    int ret = generate_cs_artifact_bpf_header(cs_path, bpf_header_path.c_str());
    if (ret) {
      fprintf(stderr, "Warning: Failed to generate cs_artifact.bpf.h, continuing anyway\n");
    }
  } else {
    fprintf(stderr, "CS file %s does not exist or is empty, skipping cs_artifact.bpf.h generation\n", cs_path);
    // Create an empty cs_artifact.bpf.h file to avoid compilation errors
    std::ofstream empty_header(bpf_header_path, std::ios::out | std::ios::trunc);
    if (empty_header.is_open()) {
      empty_header << "// Empty cs_artifact.bpf.h - no critical spans defined\n";
      empty_header << "#ifndef __CS_ARTIFACT_BPF_H__\n";
      empty_header << "#define __CS_ARTIFACT_BPF_H__\n";
      empty_header << "#endif\n";
      empty_header.close();
      fprintf(stderr, "Created empty cs_artifact.bpf.h\n");
    }
  }
  
  // Recompile BPF files in bpf_kprobe directory
  // Use the current_path already declared above
  std::string bpf_kprobe_dir = current_path.string();
  
  // Recompile all BPF object files using make
  // Find all .bpf.c files and compile them
  fprintf(stderr, "Recompiling BPF files in %s...\n", bpf_kprobe_dir.c_str());
  
  std::string bpf_examples_dir = bpf_kprobe_dir + "/bpf/examples";
  if (std::filesystem::exists(bpf_examples_dir)) {
    for (const auto &entry : std::filesystem::directory_iterator(bpf_examples_dir)) {
      if (entry.is_regular_file() && entry.path().extension() == ".c" && 
          entry.path().string().find(".bpf.c") != std::string::npos) {
        std::string bpf_c_file = entry.path().string();
        std::string bpf_o_file = bpf_c_file.substr(0, bpf_c_file.length() - 2) + ".o";
        
        // Compile using clang with BPF flags
        std::string compile_cmd = "clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -Ibpf/ -I/usr/include/bpf -c " + 
                                  bpf_c_file + " -o " + bpf_o_file + " 2>&1";
        int compile_ret = system(compile_cmd.c_str());
        if (compile_ret != 0) {
          fprintf(stderr, "Warning: Failed to compile %s\n", bpf_c_file.c_str());
        } else {
          fprintf(stderr, "Compiled: %s -> %s\n", bpf_c_file.c_str(), bpf_o_file.c_str());
        }
      }
    }
  }
  
  fprintf(stderr, "BPF recompilation completed\n");

  for (const auto &file : files) {
    std::string BPF_FILE = file;

    loaders.push_back(new XKernelLoader(BPF_FILE.c_str(), FLAGS_pin));

    // Only load critical spans if cs_path exists and is not empty
    if (std::filesystem::exists(cs_path)) {
      std::ifstream cs_file(cs_path);
      if (cs_file.is_open()) {
        std::string line;
        bool has_content = false;
        if (std::getline(cs_file, line)) {
          if (!line.empty() && line.find_first_not_of(" \t\n\r") != std::string::npos) {
            has_content = true;
          }
        }
        cs_file.close();
        
        if (has_content) {
          int ret = loaders.back()->load_cricial_spans(cs_path);
          if (ret) {
            fprintf(stderr, "Warning: Failed to load critical spans, continuing anyway\n");
          }
        } else {
          fprintf(stderr, "CS file %s is empty, skipping critical spans loading\n", cs_path);
        }
      } else {
        fprintf(stderr, "Warning: Cannot open CS file %s, skipping critical spans loading\n", cs_path);
      }
    } else {
      fprintf(stderr, "CS file %s does not exist, skipping critical spans loading\n", cs_path);
    }

    if (loaders.back()->attach_all_progs()) {
      fprintf(stderr, "Failed to attach all programs for %s\n", file.c_str());
      return 1;
    }
  }

  if (FLAGS_pin) {
    return 0;
  }

  if (FLAGS_quiet) {
    printf(
        "Kprobe attached successfully. Check /sys/kernel/tracing/trace_pipe\n");
    while (1) {
      for (auto &loader : loaders) {
        loader->dump_stack_trace();
      }
      sleep(5);
    }
  } else {
    FILE *fp = fopen("/sys/kernel/tracing/trace_pipe", "r");
    if (fp == NULL) {
      fprintf(stderr, "Failed to open /sys/kernel/tracing/trace_pipe\n");
      return 1;
    }
    int fd = fileno(fp);
    
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);

    char line[1024];

    auto last_print_st = std::chrono::steady_clock::now();
    last_print_st = std::chrono::steady_clock::now();
    while (1) {
      if (fgets(line, sizeof(line), fp) != NULL)
        printf("%s", line);
      else if (errno != EAGAIN) {
        fprintf(stderr, "Error reading from trace_pipe: %s\n", strerror(errno));
        break;
      }

      auto now = std::chrono::steady_clock::now();
      if (now - last_print_st > std::chrono::seconds(5)) {
        for (auto &loader : loaders) {
          loader->dump_stack_trace();
        }
        last_print_st = now;
      }
    }
    fclose(fp);
  }

  return 0;
}