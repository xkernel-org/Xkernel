#define _GNU_SOURCE
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <setjmp.h>
#include <sys/mman.h>
#include <unistd.h>

#ifndef MADV_GUARD_INSTALL
# define MADV_GUARD_INSTALL 102   /* Linux 6.13+ UAPI */
# define MADV_GUARD_REMOVE  103
#endif

/*
command:

gcc -std=gnu11 -O2 -pthread -Wall t.c -o t

sudo strace -ff -e trace=madvise -o trace ./t

sudo rm trace*

*/


static char *region;
static size_t rlen;
static _Atomic int stop;

/* 每个线程自己的跳转环境 */
static __thread sigjmp_buf jb;

/* SIGSEGV 处理器（纯 C 版） */
static void segv_handler(int sig, siginfo_t *si, void *uctx) {
  (void)sig; (void)uctx;
  void *addr = si->si_addr;
  if (addr >= (void*)region && addr < (void*)(region + rlen)) {
    /* 在 guard 区间内被撞：跳回该线程的安全点，继续施压 */
    siglongjmp(jb, 1);
  }
  _exit(128 + SIGSEGV); /* 其他地址的崩溃：直接退出 */
}

/* 安装备用信号栈 + SA_SIGINFO 处理器 */
static void install_sigsegv_handler(void) {
  stack_t ss = {0};
  ss.ss_sp = malloc(SIGSTKSZ);
  ss.ss_size = SIGSTKSZ;
  ss.ss_flags = 0;
  if (sigaltstack(&ss, NULL) != 0) {
    perror("sigaltstack");
    exit(1);
  }

  struct sigaction sa = {0};
  sa.sa_flags = SA_SIGINFO | SA_ONSTACK;
  sa.sa_sigaction = segv_handler;
  sigemptyset(&sa.sa_mask);
  if (sigaction(SIGSEGV, &sa, NULL) != 0) {
    perror("sigaction");
    exit(1);
  }
}

static void *thr_fn(void *arg) {
  (void)arg;
  /* 设置“安全点”：从 segv_handler 的 siglongjmp 会回到这里 */
  if (sigsetjmp(jb, 1) != 0) {
    /* 从 SIGSEGV 返回后会先到这里，再继续 while 循环 */
  }

  while (!stop) {
    for (size_t off = 0; off < rlen && !stop; off += 4096) {
      region[off]++; /* 若该页被装成 guard，会触发 SIGSEGV -> 跳回 */
    }
  }
  return NULL;
}

int main() {
  install_sigsegv_handler();

  long ncpu = sysconf(_SC_NPROCESSORS_ONLN);
  int nthreads = (int)(ncpu > 0 ? ncpu * 2 : 8);

  rlen = 256UL * 1024 * 1024; /* 256 MiB，可按需调大 */
  region = mmap(NULL, rlen, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
  if (region == MAP_FAILED) { perror("mmap"); return 1; }
  memset(region, 0, rlen); /* 先把页建起来，便于触发“zap+重试” */

  pthread_t *ts = (pthread_t*)calloc(nthreads, sizeof(*ts));
  for (int i = 0; i < nthreads; i++) pthread_create(&ts[i], NULL, thr_fn, NULL);

  for (int iter = 0; iter < 2000; iter++) {
    int rc = madvise(region, rlen, MADV_GUARD_INSTALL);
    if (rc != 0) perror("madvise(INSTALL)");
    madvise(region, rlen, MADV_GUARD_REMOVE);
  }

  stop = 1;
  for (int i = 0; i < nthreads; i++) pthread_join(ts[i], NULL);

  return 0;
}
