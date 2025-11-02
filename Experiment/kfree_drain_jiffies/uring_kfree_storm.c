// gcc -O2 -pthread uring_kfree_storm.c -o uring_kfree_storm
// 运行示例： ./uring_kfree_storm -t 4 -I 2000 -r 32 -p 0
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/resource.h>
#include <unistd.h>

#include <linux/io_uring.h>  // 需要较新的 linux-libc-dev (内核头)

#ifndef IORING_OFF_SQ_RING
#define IORING_OFF_SQ_RING 0ULL
#endif
#ifndef IORING_OFF_CQ_RING
#define IORING_OFF_CQ_RING 0x8000000ULL
#endif
#ifndef IORING_OFF_SQES
#define IORING_OFF_SQES    0x10000000ULL
#endif

static int entries_per_ring = 32;   // 每个 ring 的 SQ/CQ 深度
static int iters_per_thread = 1000; // 每个线程创建/销毁多少个 ring
static int threads = 1;             // 线程数
static int pause_ms = 0;            // 每次创建/销毁之间的停顿

static atomic_long total_rings = 0;

static inline int uring_setup(unsigned entries, struct io_uring_params *p)
{
    memset(p, 0, sizeof(*p));
    return (int)syscall(__NR_io_uring_setup, entries, p);
}

static inline int uring_register(int ring_fd, unsigned int op, const void *arg, unsigned int nr_args)
{
    return (int)syscall(__NR_io_uring_register, ring_fd, op, arg, nr_args);
}

static inline int uring_enter(int ring_fd, unsigned to_submit, unsigned min_complete, unsigned flags)
{
    return (int)syscall(__NR_io_uring_enter, ring_fd, to_submit, min_complete, flags, NULL, 0);
}

static void* worker(void *arg)
{
    (void)arg;
    for (int it = 0; it < iters_per_thread; it++) {
        struct io_uring_params p;
        int fd = uring_setup(entries_per_ring, &p);
        if (fd < 0) {
            perror("io_uring_setup");
            // 打开文件数不够时，稍等重试
            usleep(1000);
            continue;
        }

        // 计算 ring 映射大小（最小 mmap，使内核真正完成 ctx 初始化）
        size_t sq_ring_sz = p.sq_off.array + p.sq_entries * sizeof(__u32);
        size_t cq_ring_sz = p.cq_off.cqes  + p.cq_entries * sizeof(struct io_uring_cqe);
        size_t sqes_sz    = p.sq_entries * sizeof(struct io_uring_sqe);

        void *sq_ring = mmap(NULL, sq_ring_sz, PROT_READ|PROT_WRITE,
                             MAP_SHARED|MAP_POPULATE, fd, IORING_OFF_SQ_RING);
        if (sq_ring == MAP_FAILED) {
            perror("mmap SQ_RING");
            close(fd);
            continue;
        }
        void *cq_ring = mmap(NULL, cq_ring_sz, PROT_READ|PROT_WRITE,
                             MAP_SHARED|MAP_POPULATE, fd, IORING_OFF_CQ_RING);
        if (cq_ring == MAP_FAILED) {
            perror("mmap CQ_RING");
            munmap(sq_ring, sq_ring_sz);
            close(fd);
            continue;
        }
        void *sqes = mmap(NULL, sqes_sz, PROT_READ|PROT_WRITE,
                          MAP_SHARED|MAP_POPULATE, fd, IORING_OFF_SQES);
        if (sqes == MAP_FAILED) {
            perror("mmap SQES");
            munmap(cq_ring, cq_ring_sz);
            munmap(sq_ring, sq_ring_sz);
            close(fd);
            continue;
        }

        // 不提交任何 I/O；立即拆 ring（产生大量 teardown 释放）
        munmap(sqes, sqes_sz);
        munmap(cq_ring, cq_ring_sz);
        munmap(sq_ring, sq_ring_sz);
        close(fd);

        atomic_fetch_add_explicit(&total_rings, 1, memory_order_relaxed);

        if (pause_ms > 0) {
            usleep((useconds_t)pause_ms * 1000);
        }
    }
    return NULL;
}

static void set_nofile_rlimit(long want)
{
    struct rlimit rl;
    if (getrlimit(RLIMIT_NOFILE, &rl) == 0) {
        if (rl.rlim_cur < (rlim_t)want) {
            rl.rlim_cur = (rlim_t)want;
            if (rl.rlim_max < rl.rlim_cur) rl.rlim_max = rl.rlim_cur;
            setrlimit(RLIMIT_NOFILE, &rl);
        }
    }
}

static void usage(const char *prog)
{
    fprintf(stderr,
        "Usage: %s [-t threads] [-I iters_per_thread] [-r entries_per_ring] [-p pause_ms]\n"
        "Defaults: -t 1 -I 1000 -r 32 -p 0\n", prog);
}

int main(int argc, char **argv)
{
    int opt;
    while ((opt = getopt(argc, argv, "t:I:r:p:h")) != -1) {
        switch (opt) {
        case 't': threads = atoi(optarg); break;
        case 'I': iters_per_thread = atoi(optarg); break;
        case 'r': entries_per_ring = atoi(optarg); break;
        case 'p': pause_ms = atoi(optarg); break;
        case 'h': default: usage(argv[0]); return 1;
        }
    }

    // 为避免 “Too many open files”，稍微调大 ulimit
    set_nofile_rlimit(1024 * 1024);

    pthread_t *ths = calloc(threads, sizeof(*ths));
    if (!ths) { perror("calloc"); return 1; }

    for (int i = 0; i < threads; i++) {
        if (pthread_create(&ths[i], NULL, worker, NULL) != 0) {
            perror("pthread_create");
            return 1;
        }
    }
    for (int i = 0; i < threads; i++) pthread_join(ths[i], NULL);

    printf("Done. Total rings created/destroyed: %ld\n", atomic_load(&total_rings));
    return 0;
}
