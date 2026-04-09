#define _GNU_SOURCE
#include <string.h>
#include <getopt.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>

static size_t P;
FILE *output_file = NULL;

static uint64_t now_us(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (uint64_t)ts.tv_sec * 1000000ull + ts.tv_nsec / 1000ull;
}

/*
static void touch_write(unsigned char *p, size_t len, size_t stride) {
  volatile unsigned char *v = p;
  for (size_t i = 0; i < len; i += stride)
    v[i]++; // dirty each stride (typically a page)
}
*/

/*
static inline uint64_t xorshift64(uint64_t *state){
    uint64_t x = *state; x ^= x<<13; x ^= x>>7; x ^= x<<17; return *state = x ? x : 0x9e3779b97f4a7c15ULL;
}
static void touch_write(unsigned char *p, size_t len, size_t stride){
    uint64_t s = (uintptr_t)p ^ 0x9e3779b97f4a7c15ULL;
    for (size_t i = 0; i < len; i += sizeof(uint64_t)) {
        uint64_t r = xorshift64(&s);
        *(uint64_t *)(p + i) = r;
    }
}
*/


static inline uint64_t xs(uint64_t *s){ uint64_t x=*s; x^=x<<13; x^=x>>7; x^=x<<17; return *s = x ? x : 0x9e3779b97f4a7c15ULL; }

// For every 64B, write 8B randomly and leave other bytes 0
static void touch_write(unsigned char *p, size_t len, size_t stride){
    uint64_t s = (uintptr_t)p ^ 0x9e3779b97f4a7c15ULL;
    memset(p, 0, len);
    for (size_t i = 0; i < len; i += 64) {
      *(uint64_t *)(p + i) = xs(&s);
    }
}

static uint64_t touch_read(unsigned char *p, size_t len, size_t stride) {
  volatile unsigned char *v = p;
  uint64_t s = 0;
  for (size_t i = 0; i < len; i += stride)
    s += v[i];
  return s;
}

static void pageout(void *addr, size_t len) {
#ifdef MADV_PAGEOUT
  (void)madvise(addr, len, MADV_PAGEOUT);
#endif
}

static int read_major_delta(uint64_t *maj_out) {
  FILE *f = fopen("/proc/self/stat", "r");
  if (!f)
    return -1;
  int pid;
  char comm[256], st;
  if (fscanf(f, "%d (%255[^)]) %c", &pid, comm, &st) != 3) {
    fclose(f);
    return -1;
  }
  unsigned long x, minflt, majflt;
  for (int i = 4; i <= 9; i++)
    if (fscanf(f, " %lu", &x) != 1) {
      fclose(f);
      return -1;
    }
  if (fscanf(f, " %lu", &minflt) != 1) {
    fclose(f);
    return -1;
  } // field 10
  if (fscanf(f, " %lu", &x) != 1) {
    fclose(f);
    return -1;
  } // cminflt
  if (fscanf(f, " %lu", &majflt) != 1) {
    fclose(f);
    return -1;
  } // field 12
  fclose(f);
  static uint64_t prev = 0;
  if (maj_out) {
    *maj_out = prev ? ((uint64_t)majflt - prev) : 0;
  }
  prev = (uint64_t)majflt;
  return 0;
}

int main(int argc, char **argv) {
  setvbuf(stdout, NULL, _IOLBF, 0); 
  setvbuf(stderr, NULL, _IONBF, 0); 

  P = (size_t)sysconf(_SC_PAGESIZE);

  // defaults tuned to fill pool quickly under ~1.2 GiB limit
  size_t total_mb = 6144;   // total anon
  size_t block_pages = 128; // ≈ 512 KiB
  int reuse_dist = 4;       // revisit distance in blocks
  int loops = 20000;
  size_t stride = P; // 4 KiB
  int sleep_us = 0;
  bool do_pageout = false; // default OFF now
  int warmup_passes = 2;   // write entire ring N times
  int burst = 8;           // write N blocks per iter
  const char *output_filepath = NULL;

  static struct option opts[] = {{"total-mb", required_argument, 0, 1},
                                 {"block-pages", required_argument, 0, 2},
                                 {"reuse-dist", required_argument, 0, 3},
                                 {"loops", required_argument, 0, 4},
                                 {"stride", required_argument, 0, 5},
                                 {"sleep-us", required_argument, 0, 6},
                                 {"pageout", no_argument, 0, 7},
                                 {"warmup-passes", required_argument, 0, 8},
                                 {"burst", required_argument, 0, 9},
                                 {"file", required_argument, 0, 10},
                                 {0, 0, 0, 0}};
  int c, idx;
  while ((c = getopt_long(argc, argv, "", opts, &idx)) != -1) {
    switch (c) {
    case 1:
      total_mb = strtoull(optarg, NULL, 0);
      break;
    case 2:
      block_pages = strtoull(optarg, NULL, 0);
      break;
    case 3:
      reuse_dist = atoi(optarg);
      break;
    case 4:
      loops = atoi(optarg);
      break;
    case 5:
      stride = strtoull(optarg, NULL, 0);
      break;
    case 6:
      sleep_us = atoi(optarg);
      break;
    case 7:
      do_pageout = true;
      break;
    case 8:
      warmup_passes = atoi(optarg);
      break;
    case 9:
      burst = atoi(optarg);
      break;
    case 10:
      output_filepath = optarg;
      break;
    default:
      fprintf(stderr,
              "Usage: %s [--total-mb MB] [--block-pages N] [--reuse-dist N]\n"
              "          [--loops N] [--stride B] [--sleep-us US] [--pageout]\n"
              "          [--warmup-passes N] [--burst N] [--file </path/to/file>]\n",
              argv[0]);
      return 1;
    }
  }

  if (output_filepath) {
    // Set the umask to ensure file creation with normal permissions (rw-r--r--)
    umask(0000);  // No restrictions on permissions for the new file

    // Open the file with normal user permissions
    int fd = open(output_filepath, O_WRONLY | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH);
    if (fd == -1) {
      perror("Error opening output file");
      return 1;
    }
    output_file = fdopen(fd, "w");
    if (!output_file) {
      perror("Error associating file stream");
      close(fd);
      return 1;
    }

    // Change file ownership to the current user (if necessary)
    if (getuid() != 0) {
      if (chown(output_filepath, getuid(), getgid()) == -1) {
        perror("Failed to change file ownership");
      }
    }
  } else {
    output_file = stderr;
  }

  // the bytes contained in one block
  const size_t block_bytes = block_pages * P;
  const size_t total_bytes = total_mb * 1024ull * 1024ull;
  if (block_bytes == 0 || total_bytes < block_bytes) {
    fprintf(stderr, "bad sizes\n");
    return 1;
  }
  const size_t blocks = total_bytes / block_bytes;

  fprintf(stderr,
          "[cfg] total=%.2fGiB blocks=%zu block=%zu pages(≈%zuKiB) reuse=%d "
          "stride=%zu pageout=%s warmup=%d burst=%d\n",
          total_bytes / 1024.0 / 1024 / 1024, blocks, block_pages,
          block_bytes / 1024, reuse_dist, stride, do_pageout ? "on" : "off",
          warmup_passes, burst);
  fflush(stderr); 

  unsigned char *buf = mmap(NULL, total_bytes, PROT_READ | PROT_WRITE,
                            MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  if (buf == MAP_FAILED) {
    perror("mmap");
    return 1;
  }

  // pre-touch first byte per block (create VMAs)
  for (size_t b = 0; b < blocks; b++)
    buf[b * block_bytes] = (unsigned char)b;

  // WARMUP: write entire ring warmup_passes times (no revisit), to fill zswap quickly
  for (int p = 0; p < warmup_passes; p++) {
    uint64_t last = now_us();
    for (size_t b = 0; b < blocks; b++) {
      touch_write(buf + b * block_bytes, block_bytes, stride);

      uint64_t t = now_us();
      if (t - last >= 500000) { // ~0.5s 打印一次进度
        double pct = 100.0 * (double)(b + 1) / (double)blocks;
        fprintf(stderr, "[warmup %d/%d] %.2f%%\n", p + 1, warmup_passes, pct);
        fflush(stderr);
        last = t;
      }
    }
  }

  uint64_t majd = 0;
  (void)read_major_delta(&majd); // baseline

  for (int it = 0; it < loops; it++) {
    uint64_t t0 = now_us();

    // burst writes, also access by batch--batch size is burst
    // e.g. when burst = 12, in one loop, adjcent 12 blocks will be accessed
    // 0 - 11, 12 - 23...
    for (int k = 0; k < burst; k++) {
      size_t g = ((size_t)it * (size_t)burst + (size_t)k) % blocks;
      touch_write(buf + g * block_bytes, block_bytes, stride);

      if (do_pageout && blocks > 1) {
        size_t prev = (g + blocks - 1) % blocks;
        pageout(buf + prev * block_bytes, block_bytes);
      }

      // reuse: revisit reuse_dist-behind block
      size_t r = (g + blocks - (size_t)reuse_dist) % blocks;
      (void)touch_read(buf + r * block_bytes, block_bytes, stride);
    }

    uint64_t t1 = now_us();
    (void)read_major_delta(&majd);
    fprintf(output_file, "iter=%d dmajflt=%" PRIu64 " dt_us=%" PRIu64 "\n", it, majd, (t1 - t0));
    fflush(output_file); 

    if (sleep_us > 0)
      usleep(sleep_us);
  }

  munmap(buf, total_bytes);
  if (output_file != stderr) {
    fclose(output_file);
  }
  return 0;
}
