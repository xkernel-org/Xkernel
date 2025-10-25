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

#include "loader_common.h"

using namespace xkernel;

DEFINE_string(files, "", "BPF files to load, separated by comma");
DEFINE_bool(list, false, "List all available BPF files");
DEFINE_bool(quiet, false, "Quiet mode, do not print any output");
DEFINE_bool(one_shot, false, "One shot mode, run BPF programs once and exit");

#define BPF_DIR "bpf/examples/"

std::vector<XKernelLoader *> loaders;

// Utility function to receive a message from netlink socket
// Returns the number of bytes received, or <0 on error.
// The buffer must be large enough to hold the message.
ssize_t recv_netlink_msg(int sock_fd, char *buf, size_t buf_sz) {
  struct sockaddr_nl nl_addr;
  struct iovec iov = {
    .iov_base = buf,
    .iov_len = buf_sz,
  };
  struct msghdr msg = {
    .msg_name = &nl_addr,
    .msg_namelen = sizeof(nl_addr),
    .msg_iov = &iov,
    .msg_iovlen = 1,
    .msg_control = NULL,
    .msg_controllen = 0,
    .msg_flags = 0,
  };

  ssize_t ret = recvmsg(sock_fd, &msg, 0);
  if (ret < 0) {
    if (errno != EAGAIN)
      perror("recv_netlink_msg: recvmsg failed");
    return ret;
  }

  // Safety: ensure null-termination if possible
  if ((size_t)ret < buf_sz)
    buf[ret] = '\0';
  else if (buf_sz > 0)
    buf[buf_sz-1] = '\0';

  return ret;
}


int main(int argc, char *argv[]) {
  gflags::ParseCommandLineFlags(&argc, &argv, true);

  signal(SIGINT, [](int) {
    for (auto loader : loaders) {
      delete loader;
    }
    exit(0);
  });

  // Initialize netlink
  struct sockaddr_nl src_addr;
  int sock_fd;
  char netlink_msg[1024];

  sock_fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_USERSOCK);

  int flags = fcntl(sock_fd, F_GETFL, 0);
  fcntl(sock_fd, F_SETFL, flags | O_NONBLOCK);

  memset(&src_addr, 0, sizeof(src_addr));
  src_addr.nl_family = AF_NETLINK;
  src_addr.nl_pid = getpid();
  src_addr.nl_groups = 0;
  bind(sock_fd, (struct sockaddr *)&src_addr, sizeof(src_addr));

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

    loaders.push_back(new XKernelLoader(BPF_FILE.c_str(), FLAGS_one_shot));

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

      if (recv_netlink_msg(sock_fd, netlink_msg, sizeof(netlink_msg)) > 0) {
        char *payload = (char *)NLMSG_DATA(netlink_msg);
        if (strncmp(payload, "1", 1) == 0) {
          printf("Instruction Rewriting Kprobes enabled\n");
          for (auto &loader : loaders) {
            loader->update_transition_map(1);
          }
        } else {
          printf("Instruction Rewriting Kprobes disabled\n");
          for (auto &loader : loaders) {
            loader->update_transition_map(0);
          }
        }
      }
    }
    fclose(fp);
  }

  return 0;
}