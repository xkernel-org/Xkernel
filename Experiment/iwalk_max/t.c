// build: gcc -O2 -Wall t.c -o t
// run:   sudo ./t /mnt/xfs_test   // 换成你的 XFS 挂载点

// ---- 兼容垫片：在包含 xfs_fs.h 之前补齐缺失符号 ----
#ifndef __user
#define __user
#endif
#ifndef __force
#define __force
#endif
#ifndef __iomem
#define __iomem
#endif

#include <linux/types.h>
#include <sys/types.h>
#include <stdint.h>

// 一些发行版的 xfslibs-dev 头在独立程序里不会自动拉到这些 typedef
// 资料：prid_t 是 32bit 的 Project ID；xfs_off_t 是有符号 64bit 文件偏移。
typedef uint32_t prid_t;     // ref: XFS xfs_types.h
typedef int64_t  xfs_off_t;  // ref: XFS docs: "xfs_off_t: Signed 64 bit file offset"

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <xfs/xfs_fs.h>   // ioctl_xfs_bulkstat(2) / ioctl_xfs_inumbers(2)

// 把这两个数设得远大于内核上限，以命中 cap 逻辑：
#define BULKSTAT_REQ  8192     // > IWALK_MAX_INODE_PREFETCH(2048)
#define INUMBERS_REQ  65536    // > MAX_INOBT_WALK_PREFETCH(一页能放下的inobt记录数)

static void die(const char *msg) { perror(msg); exit(1); }

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: sudo %s <xfs-mountpoint>\n", argv[0]);
        return 2;
    }
    int fd = open(argv[1], O_RDONLY | O_DIRECTORY);
    if (fd < 0) die("open mountpoint");

    // ---------- 1) 触发 IWALK_MAX_INODE_PREFETCH 路径 (BULKSTAT v5) ----------
    size_t bsz = sizeof(struct xfs_bulkstat_req)
               + (size_t)BULKSTAT_REQ * sizeof(struct xfs_bulkstat);
    struct xfs_bulkstat_req *bs = calloc(1, bsz);
    if (!bs) die("calloc bulkstat");
    bs->hdr.ino    = 0;              // 从第一个 inode 开始
    bs->hdr.flags  = 0;              // 最简
    bs->hdr.icount = BULKSTAT_REQ;   // 故意给大，命中 2048 的 cap

    if (ioctl(fd, XFS_IOC_BULKSTAT, bs) < 0) {
        free(bs);
        die("ioctl(XFS_IOC_BULKSTAT)");
    }
    printf("[BULKSTAT] requested=%u, returned=%u\n",
           bs->hdr.icount, bs->hdr.ocount);
    if (bs->hdr.ocount > 0) {
        const struct xfs_bulkstat *r = &bs->bulkstat[0];
        printf("  first inode: ino=%llu size=%llu nlink=%u mode=%o\n",
               (unsigned long long)r->bs_ino,
               (unsigned long long)r->bs_size,
               r->bs_nlink, r->bs_mode);
    }
    free(bs);

    // ---------- 2) 触发 MAX_INOBT_WALK_PREFETCH 路径 (INUMBERS v5) ----------
    size_t isz = sizeof(struct xfs_inumbers_req)
               + (size_t)INUMBERS_REQ * sizeof(struct xfs_inumbers);
    struct xfs_inumbers_req *in = calloc(1, isz);
    if (!in) die("calloc inumbers");
    in->hdr.ino    = 0;              // 从第一个 inode 开始
    in->hdr.flags  = 0;
    in->hdr.icount = INUMBERS_REQ;   // 故意给大，命中“每页上限”的 cap

    if (ioctl(fd, XFS_IOC_INUMBERS, in) < 0) {
        free(in);
        die("ioctl(XFS_IOC_INUMBERS)");
    }
    printf("[INUMBERS] requested=%u, returned=%u\n",
           in->hdr.icount, in->hdr.ocount);
    if (in->hdr.ocount > 0) {
        const struct xfs_inumbers *g = &in->inumbers[0];
        printf("  first group: startino=%llu alloccount=%u allocmask=0x%llx\n",
               (unsigned long long)g->xi_startino,
               g->xi_alloccount,
               (unsigned long long)g->xi_allocmask);
    }
    free(in);

    close(fd);
    return 0;
}
