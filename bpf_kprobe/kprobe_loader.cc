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

#include "loader_common.h"

using namespace xkernel;

DEFINE_string(files, "", "BPF files to load, separated by comma");
DEFINE_bool(quiet, false, "Quiet mode, do not print any output");
DEFINE_bool(pin, false, "Pin the BPF objects to the file system");
DEFINE_bool(one_shot, false, "One shot mode, run BPF programs once and exit");

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

  for (const auto &file : files) {
    std::string BPF_FILE = file;

    loaders.push_back(new XKernelLoader(BPF_FILE.c_str(), FLAGS_one_shot, FLAGS_pin));

    int ret = loaders.back()->load_cricial_spans("/dev/shm/xkernel/cs");
    if (ret) {
      fprintf(stderr, "Failed to load critical spans\n");
      return 1;
    }

    if (FLAGS_one_shot) {
      if (loaders.back()->attach_all_progs_one_shot()) {
        fprintf(stderr, "Failed to attach all programs (one-shot) for %s\n", file.c_str());
        return 1;
      }
    } else {
      if (loaders.back()->attach_all_progs()) {
        fprintf(stderr, "Failed to attach all programs for %s\n", file.c_str());
        return 1;
      }
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