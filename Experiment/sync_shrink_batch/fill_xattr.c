#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/limits.h>
#include <pthread.h>
#include <sched.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h>
#include <sys/stat.h>
#include <sys/sysinfo.h>
#include <sys/types.h>
#include <sys/xattr.h>
#include <unistd.h>

// command: sudo ./fill_xattr /mnt/x/xx 32 120000 512
// sudo find /mnt/x -xdev -mindepth 1 -delete


static ssize_t fill_random(void *buf, size_t len) {
    ssize_t n = getrandom(buf, len, 0);
    if (n >= 0) return n;
    if (errno != ENOSYS && errno != EPERM) return -1;
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) return -1;
    size_t off = 0;
    while (off < len) {
        ssize_t r = read(fd, (char*)buf + off, len - off);
        if (r <= 0) { close(fd); return -1; }
        off += (size_t)r;
    }
    close(fd);
    return (ssize_t)len;
}

typedef struct {
    const char *basedir;
    int tid, nthreads;
    long files_per_thread;
    size_t val_bytes;
} Work;

static void *worker(void *arg) {
    Work *w = (Work*)arg;
    char dir[PATH_MAX];
    snprintf(dir, sizeof(dir), "%s/t%02d", w->basedir, w->tid);

    if (mkdir(dir, 0755) && errno != EEXIST) {
        fprintf(stderr, "mkdir(%s): %s\n", dir, strerror(errno));
        return NULL;
    }

    unsigned char *val = malloc(w->val_bytes);
    if (!val) { perror("malloc"); return NULL; }

    char path[PATH_MAX];
    for (long i = 0; i < w->files_per_thread; i++) {
        snprintf(path, sizeof(path), "%s/f%06ld", dir, i);
        int fd = open(path, O_CREAT | O_EXCL | O_WRONLY, 0644);
        if (fd >= 0) close(fd);
        else if (errno != EEXIST) {
            fprintf(stderr, "open(%s): %s\n", path, strerror(errno));
            break;
        }

        if (fill_random(val, w->val_bytes) < 0) { perror("getrandom"); break; }
        /* 注入 (tid,i) 到前 16B，确保“唯一性”且稳定超过 inode 内联阈值 */
        if (w->val_bytes >= 16) {
            *((uint64_t*)val)     ^= (uint64_t)w->tid;
            *((uint64_t*)(val+8)) ^= (uint64_t)i;
        }

        if (setxattr(path, "user.test", val, w->val_bytes, 0) < 0) {
            if (errno == ENOTSUP) {
                fprintf(stderr, "setxattr ENOTSUP: 请确认 ext4 且启用 user_xattr，未使用 nombcache\n");
            } else {
                fprintf(stderr, "setxattr(%s): %s\n", path, strerror(errno));
            }
            break;
        }

        if ((i & 0x7FF) == 0) { // 每 2048 次打印一次
            fprintf(stdout, "T%02d progress: %ld\n", w->tid, i);
            fflush(stdout);
        }
    }

    free(val);
    return NULL;
}

int main(int argc, char **argv) {
    const char *basedir = "/mnt/x/xx";
    int nthreads = (int)sysconf(_SC_NPROCESSORS_ONLN);
    long total_files = 120000;   // 总文件数（按 2GiB 镜像留足余量）
    size_t val_bytes = 512;      // 让 xattr 超过内联，走外部块 ⇒ 进入 mbcache

    if (argc >= 2) basedir = argv[1];
    if (argc >= 3) nthreads = atoi(argv[2]);
    if (argc >= 4) total_files = strtol(argv[3], NULL, 10);
    if (argc >= 5) val_bytes = (size_t)strtoul(argv[4], NULL, 10);

    if (mkdir(basedir, 0755) && errno != EEXIST) {
        fprintf(stderr, "mkdir(%s): %s\n", basedir, strerror(errno));
        return 1;
    }
    // 预创建每个线程的子目录，避免单目录哈希竞争
    for (int t = 0; t < nthreads; t++) {
        char sub[PATH_MAX];
        snprintf(sub, sizeof(sub), "%s/t%02d", basedir, t);
        if (mkdir(sub, 0755) && errno != EEXIST) {
            fprintf(stderr, "mkdir(%s): %s\n", sub, strerror(errno));
            return 1;
        }
    }

    long per = total_files / nthreads + (total_files % nthreads != 0);
    pthread_t *ths = calloc(nthreads, sizeof(*ths));
    Work *works = calloc(nthreads, sizeof(*works));
    if (!ths || !works) { perror("calloc"); return 1; }

    for (int t = 0; t < nthreads; t++) {
        works[t] = (Work){ .basedir=basedir, .tid=t, .nthreads=nthreads,
                           .files_per_thread=per, .val_bytes=val_bytes };
        pthread_create(&ths[t], NULL, worker, &works[t]);
    }
    for (int t = 0; t < nthreads; t++) pthread_join(ths[t], NULL);

    free(ths); free(works);
    fprintf(stdout, "DONE. target total files ~%ld under %s\n", per * nthreads, basedir);
    return 0;
}
