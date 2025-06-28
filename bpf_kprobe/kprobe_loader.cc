// SPDX-License-Identifier: GPL-2.0
#include <bpf/libbpf.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>

#include <dirent.h>
#include <gflags/gflags.h>
#include <sstream>
#include <string>
#include <vector>

#include "loader_common.h"

using namespace xkernel;

DEFINE_string(files, "", "BPF files to load, separated by comma");
DEFINE_bool(list, false, "List all available BPF files");
DEFINE_bool(quiet, false, "Quiet mode, do not print any output");

#define BPF_DIR "bpf/examples/"

int main(int argc, char *argv[]) {
  gflags::ParseCommandLineFlags(&argc, &argv, true);

  if (FLAGS_list) {
    // list all files in BPF_DIR
    DIR *dir = opendir(BPF_DIR);
    if (dir == NULL) {
      fprintf(stderr, "Failed to open %s\n", BPF_DIR);
      return 1;
    }
    printf("Available BPF files:\n");
    struct dirent *entry;
    int cnt = 0;
    while ((entry = readdir(dir)) != NULL) {
      if (strstr(entry->d_name, ".bpf.o") != NULL) {
        printf("[%d] %s\n", cnt++, entry->d_name);
      }
    }
    closedir(dir);
    return 0;
  }

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

  if (FLAGS_quiet) {
    printf(
        "Kprobe attached successfully. Check /sys/kernel/tracing/trace_pipe\n");
    while (1) {
      sleep(1);
    }
  } else {
    FILE *fp = fopen("/sys/kernel/tracing/trace_pipe", "r");
    if (fp == NULL) {
      fprintf(stderr, "Failed to open /sys/kernel/tracing/trace_pipe\n");
      return 1;
    }
    char line[1024];
    while (fgets(line, sizeof(line), fp) != NULL) {
      printf("%s", line);
    }
    fclose(fp);
  }

  return 0;
}