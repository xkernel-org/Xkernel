// SPDX-License-Identifier: GPL-2.0
#include <bpf/libbpf.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>

#include <gflags/gflags.h>
#include <sstream>
#include <string>
#include <vector>

#include "loader_common.h"

using namespace xkernel;

DEFINE_string(files, "", "BPF files to load, separated by comma");

#define BPF_DIR "bpf/examples/"

int main(int argc, char *argv[]) {
  gflags::ParseCommandLineFlags(&argc, &argv, true);

  if (FLAGS_files.empty()) {
    fprintf(stderr, "files is not set\n");
    return 1;
  }

  std::vector<std::string> files;
  std::string file;
  std::istringstream ss(FLAGS_files);
  while (std::getline(ss, file, ',')) {
    if (!file.empty()) {
      files.push_back(file);
    }
  }

  for (const auto &file : files) {
    std::string BPF_FILE = BPF_DIR + file;

    XKernelLoader loader(BPF_FILE.c_str());

    if (loader.attach_all_progs()) {
      fprintf(stderr, "Failed to attach all programs for %s\n", file.c_str());
      return 1;
    }
  }

  printf(
      "Kprobe attached successfully. Check /sys/kernel/tracing/trace_pipe\n");
  while (1)
    sleep(1);
}