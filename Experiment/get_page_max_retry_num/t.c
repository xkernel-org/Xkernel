// softoffline_race.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <unistd.h>

static size_t PAGE_SZ;
static size_t N_PAGES = 64;
static uint8_t *base;
static _Atomic int cur_idx = -1;
static _Atomic unsigned long so_ok = 0, so_err = 0, cycles = 0;

static void pin_to_cpu(int cpu) {
  cpu_set_t set; CPU_ZERO(&set); CPU_SET(cpu, &set);
  pthread_setaffinity_np(pthread_self(), sizeof(set), &set);
}

static int read_pfn_for_addr(void *addr, unsigned long long *pfn_out) {
  int fd = open("/proc/self/pagemap", O_RDONLY);
  if (fd < 0) { perror("open pagemap"); return -1; }
  uint64_t vpn = (uint64_t)addr / PAGE_SZ;
  off_t off = (off_t)vpn * 8;
  if (lseek(fd, off, SEEK_SET) < 0) { perror("lseek pagemap"); close(fd); return -1; }
  uint64_t entry;
  if (read(fd, &entry, 8) != 8) { perror("read pagemap"); close(fd); return -1; }
  close(fd);
  if (!(entry & (1ULL << 63))) { fprintf(stderr, "page not present\n"); return -1; }
  *pfn_out = entry & ((1ULL << 55) - 1);
  return 0;
}

static int soft_offline_physaddr(uint64_t phys) {
  int fd = open("/sys/devices/system/memory/soft_offline_page", O_WRONLY);
  if (fd < 0) { perror("open soft_offline_page"); return -1; }
  char buf[64];
  int n = snprintf(buf, sizeof(buf), "0x%llx\n", (unsigned long long)phys);
  int rc = write(fd, buf, n);
  close(fd);
  if (rc < 0) return -1;
  return 0;
}

static void busy_pause(int iters) {
  for (int i = 0; i < iters; i++) asm volatile("pause" ::: "memory");
}

static void *shaker_thread(void *arg) {
  pin_to_cpu(0);
  for (;;) {
    for (size_t i = 0; i < N_PAGES; i++) {
      uint8_t *p = base + i * PAGE_SZ;
      atomic_store_explicit(&cur_idx, (int)i, memory_order_release);

      // 丢页 -> 下一次触碰会缺页重新分配/从 pcplist 回收
      madvise(p, PAGE_SZ, MADV_DONTNEED);

      busy_pause(200);

      // 立刻“消费”该页，制造与软下线注入的时间竞争
      *(volatile uint8_t *)p = 1;

      atomic_fetch_add_explicit(&cycles, 1, memory_order_relaxed);
    }
  }
  return NULL;
}

static void *softoffline_thread(void *arg) {
  pin_to_cpu(1);
  for (;;) {
    int i = atomic_load_explicit(&cur_idx, memory_order_acquire);
    if (i >= 0) {
      uint8_t *p = base + (size_t)i * PAGE_SZ;

      // 确保页驻留，然后查 PFN -> 物理地址
      *(volatile uint8_t *)p = 2;

      unsigned long long pfn;
      if (read_pfn_for_addr(p, &pfn) == 0) {
        uint64_t phys = (uint64_t)pfn * PAGE_SZ;
        if (soft_offline_physaddr(phys) == 0)
          atomic_fetch_add_explicit(&so_ok, 1, memory_order_relaxed);
        else
          atomic_fetch_add_explicit(&so_err, 1, memory_order_relaxed);
      } else {
        atomic_fetch_add_explicit(&so_err, 1, memory_order_relaxed);
      }
    }
    busy_pause(200);
  }
  return NULL;
}

int main(int argc, char **argv) {
  if (geteuid() != 0) {
    fprintf(stderr, "Run as root: need PFN & write /sys/.../soft_offline_page\n");
    return 1;
  }

  PAGE_SZ = (size_t)sysconf(_SC_PAGESIZE);
  if (argc >= 2) { long n = strtol(argv[1], NULL, 10); if (n > 0) N_PAGES = (size_t)n; }

  size_t len = N_PAGES * PAGE_SZ;
  base = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  if (base == MAP_FAILED) { perror("mmap"); return 1; }

  // 预触碰让每页驻留，有利于立刻拿到 PFN
  for (size_t i = 0; i < N_PAGES; i++) base[i * PAGE_SZ] = 0;

  pthread_t th1, th2;
  if (pthread_create(&th1, NULL, shaker_thread, NULL) ||
      pthread_create(&th2, NULL, softoffline_thread, NULL)) {
    perror("pthread_create"); return 1;
  }

  for (;;) {
    sleep(1);
    fprintf(stderr, "[stats] soft_offline_ok=%lu  err=%lu  cycles=%lu  pages=%zu\n",
            (unsigned long)so_ok, (unsigned long)so_err,
            (unsigned long)cycles, N_PAGES);
  }
}
