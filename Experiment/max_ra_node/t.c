// t.c — 用 FIEMAP_FLAG_CACHE 预缓存映射，然后从 >4MiB 偏移做缓冲读，触发 F2FS 节点 RA
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>

#include <linux/fs.h>       // FS_IOC_FIEMAP
#include <linux/fiemap.h>   // struct fiemap, FIEMAP_FLAG_*

#ifndef FS_IOC_FIEMAP
#  include <sys/ioctl.h>    // for _IOWR macro
#  define FS_IOC_FIEMAP _IOWR('f', 11, struct fiemap)
#endif

#ifndef FIEMAP_FLAG_CACHE
#  define FIEMAP_FLAG_CACHE 0x00000004  // request caching of the extents
#endif 

static void die(const char *msg) { perror(msg); exit(1); }

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s /mnt/f2/bigfile\n", argv[0]); return 2; }
    const char *path = argv[1];

    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) die("open");

    // --- 1) 请求内核缓存该文件的 extents（FIEMAP_FLAG_CACHE） ---
    struct {
        struct fiemap fm;
        struct fiemap_extent fe[1024];
    } fmap;
    memset(&fmap, 0, sizeof(fmap));
    fmap.fm.fm_start = 0;
    fmap.fm.fm_length = ~0ULL;
    fmap.fm.fm_flags = FIEMAP_FLAG_CACHE;
    fmap.fm.fm_extent_count = 1024;

    if (ioctl(fd, FS_IOC_FIEMAP, &fmap) < 0) {
        fprintf(stderr, "FIEMAP(CACHE): %s (继续)\n", strerror(errno));
    } else {
        fprintf(stderr, "fiemap cached %u extents\n", fmap.fm.fm_mapped_extents);
    }

    // --- 2) 从 4MiB 偏移开始做缓冲读，跨过 inode 直索引阈值，强制下钻节点 ---
    const size_t BS = 128 * 1024;       // 128KiB
    const long long OFF = 4LL * 1024 * 1024; // 4MiB
    const size_t TOTAL = 512 * 1024 * 1024;  // 512MiB
    char *buf = (char *)malloc(BS);
    if (!buf) die("malloc");

    size_t done = 0;
    while (done < TOTAL) {
        size_t nreq = (TOTAL - done) < BS ? (TOTAL - done) : BS;
        ssize_t n = pread(fd, buf, nreq, OFF + (long long)done);
        if (n <= 0) break;
        done += (size_t)n;
    }
    fprintf(stderr, "read %zu bytes starting at %lld\n", done, OFF);

    free(buf);
    close(fd);
    return 0;
}
