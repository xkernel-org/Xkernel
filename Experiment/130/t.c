// thrash_cont.c
#define _GNU_SOURCE
#include <fcntl.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>

#ifndef DIRNAME
#define DIRNAME "./streamdir"
#endif

// gcc -O2 -pthread -o t t.c

/*
整体运行的“内核视角”时间线（循环内反复发生）
程序扩容并读取新增文件区间 → 大量新文件页进入页缓存；
cgroup 使用量被压在 memory.high 附近 → memcg 回收启动；
Linux Kernel Documentation
+1
旧缓存页被回收时，workingset 为它们在 mapping 的 xarray 写入 shadow entries，并把对应 xarray 节点挂到 shadow_nodes LRU；当 shadow_nodes 数量超过阈值，count_shadow_nodes() 返回“可回收对象”；
Google Groups
+1
shrink_slab() 调用该 shrinker 的 do_shrink_slab()；因 seeks==0，delta=freeable/2，本轮回收一半影子；回收完成后 shadow_nodes 数下降；
gentwo.org
下一轮 epoch 又扩容、又读新区间 → 再次堆高 shadow_nodes → 持续触发 shrinker。
*/


static size_t file_mb_initial = 256;   // 每个文件初始大小
static size_t file_count       = 4;    // 文件个数
static size_t grow_mb_per_epoch= 128;  // 每轮每个文件额外增长
static size_t read_chunk_mb    = 4;    // 读块大小
static int    threads          = 2;    // 并发读线程数

// 压舱石控制
static volatile int ballast_on = 1;
static char *ballast = NULL;
static size_t ballast_target_mb = 64;   // 初始压舱石
static size_t ballast_cap_mb    = 1024; // 最大压舱石

// 简单读取 cgroup v2 memory 文件
static long read_cgroup_bytes(const char *name) {
    char path[256];
    snprintf(path, sizeof(path), "/sys/fs/cgroup/%s", name);
    FILE *f = fopen(path, "r");
    if(!f) return -1;
    long v = -1;
    if (fscanf(f, "%ld", &v) != 1) v = -1;
    fclose(f);
    return v; // bytes
}

static void adjust_ballast() {
    long high = read_cgroup_bytes("memory.high");
    long max  = read_cgroup_bytes("memory.max");
    long cur  = read_cgroup_bytes("memory.current");
    if (high <= 0 || max <= 0 || cur < 0) return;

    // 目标是把 usage 靠近 memory.high 的 95%，避免踩 max
    long target = (long)(high * 0.95);
    if (target > max - (64L<<20)) target = max - (64L<<20); // 离 max 留 64 MiB 缓冲
    if (target < 0) target = high;

    long need = target - cur;
    if (need > (16L<<20) && ballast_target_mb < ballast_cap_mb) {
        ballast_target_mb += 16; // 增加压舱石
    } else if (need < -(32L<<20) && ballast_target_mb > 16) {
        ballast_target_mb -= 16; // 减少压舱石
    }

    size_t want = ballast_target_mb * (1UL<<20);
    // 伸缩压舱石
    static size_t have = 0;
    if (want > have) {
        char *p = realloc(ballast, want);
        if (p) {
            ballast = p;
            memset(ballast + have, 0x5A, want - have);
            have = want;
        }
    } else if (want + (16UL<<20) < have) {
        // 逐步收缩，避免频繁 malloc/free
        have -= (16UL<<20);
        ballast = realloc(ballast, have);
    }
}

static void *ballast_thread(void *arg) {
    (void)arg;
    while (ballast_on) {
        adjust_ballast();
        usleep(200*1000);
    }
    return NULL;
}

static int ensure_dir(const char *d) {
    struct stat st;
    if (stat(d, &st) == 0) {
        if (S_ISDIR(st.st_mode)) return 0;
        errno = ENOTDIR; return -1;
    }
    if (mkdir(d, 0755) == 0) return 0;
    return -1;
}

static int grow_file(const char *path, size_t new_mb) {
    int fd = open(path, O_RDWR | O_CREAT, 0644);
    if (fd < 0) return -1;
    off_t want = (off_t)new_mb * 1024 * 1024;
    if (ftruncate(fd, want) < 0) { close(fd); return -1; }
    // 轻触使其实际分配
    size_t poke = 4*1024*1024;
    void *m = mmap(NULL, poke, PROT_READ|PROT_WRITE, MAP_SHARED, fd, want - poke);
    if (m != MAP_FAILED) { memset(m, 0xA5, poke); munmap(m, poke); }
    close(fd);
    return 0;
}

typedef struct {
    char **files;
    size_t nfiles;
    size_t from_mb;
    size_t to_mb;
} reader_args_t;

static void *reader_worker(void *arg) {
    reader_args_t *a = (reader_args_t*)arg;
    size_t chunk = read_chunk_mb * 1024UL * 1024UL;
    void *buf = malloc(chunk);
    if (!buf) return NULL;

    for (size_t i = 0; i < a->nfiles; i++) {
        const char *path = a->files[i];
        int fd = open(path, O_RDONLY);
        if (fd < 0) continue;

        off_t off = (off_t)a->from_mb * 1024 * 1024;
        off_t end = (off_t)a->to_mb   * 1024 * 1024;
        if (end <= off) { close(fd); continue; }

        // 顺序读新增区间
        while (off < end) {
            size_t to_read = (end - off) < (off_t)chunk ? (size_t)(end - off) : chunk;
            ssize_t r = pread(fd, buf, to_read, off);
            if (r <= 0) break;
            off += r;
        }
        close(fd);
    }
    free(buf);
    return NULL;
}

int main(int argc, char **argv) {
    if (argc >= 2) file_count = strtoul(argv[1], NULL, 0);
    if (argc >= 3) file_mb_initial = strtoul(argv[2], NULL, 0);
    if (argc >= 4) grow_mb_per_epoch = strtoul(argv[3], NULL, 0);

    if (ensure_dir(DIRNAME) < 0) {
        perror("mkdir streamdir"); return 1;
    }

    // 准备文件名
    char **files = calloc(file_count, sizeof(char*));
    for (size_t i = 0; i < file_count; i++) {
        files[i] = malloc(256);
        snprintf(files[i], 256, "%s/file_%zu.dat", DIRNAME, i);
        // 首次建大文件
        grow_file(files[i], file_mb_initial);
    }

    // 启动压舱石线程
    pthread_t th;
    pthread_create(&th, NULL, ballast_thread, NULL);

    size_t cur_mb = file_mb_initial;
    size_t epoch = 0;

    while (1) {
        epoch++;
        size_t new_mb = cur_mb + grow_mb_per_epoch;

        // 每轮先扩容
        for (size_t i = 0; i < file_count; i++) {
            if (grow_file(files[i], new_mb) < 0) {
                fprintf(stderr, "grow_file failed: %s\n", files[i]);
            }
        }

        // 并发读“新增区间”
        reader_args_t args = {
            .files   = files,
            .nfiles  = file_count,
            .from_mb = cur_mb,
            .to_mb   = new_mb
        };
        // 开 N 个线程跑同样范围，增压 page cache
        pthread_t *workers = calloc(threads, sizeof(pthread_t));
        for (int t = 0; t < threads; t++)
            pthread_create(&workers[t], NULL, reader_worker, &args);
        for (int t = 0; t < threads; t++)
            pthread_join(workers[t], NULL);
        free(workers);

        cur_mb = new_mb;

        // 打点输出
        long cur = read_cgroup_bytes("memory.current");
        long high= read_cgroup_bytes("memory.high");
        long mx  = read_cgroup_bytes("memory.max");
        fprintf(stderr, "[epoch %zu] files=%zu each=%zuMB  mem.cur=%.1fMB high=%.1fMB max=%.1fMB ballast=%zuMB\n",
            epoch, file_count, cur_mb, cur/1048576.0, high/1048576.0, mx/1048576.0, ballast_target_mb);

        // 小憩，让回收/scan 有时间跑
        usleep(200*1000);
    }

    ballast_on = 0; pthread_join(th, NULL);
    return 0;
}
