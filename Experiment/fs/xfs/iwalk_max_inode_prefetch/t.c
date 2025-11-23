// gcc -O2 -Wall t.c -o t

// Make sure this mount point exists:
// sudo ./t /mnt/xfs-test   

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

typedef uint32_t prid_t;     
typedef int64_t  xfs_off_t;  

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <xfs/xfs_fs.h>   // ioctl_xfs_bulkstat(2) / ioctl_xfs_inumbers(2)

#define BULKSTAT_REQ  8192     
#define INUMBERS_REQ  65536    

static void die(const char *msg) { perror(msg); exit(1); }

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: sudo %s <xfs-mountpoint>\n", argv[0]);
        return 2;
    }
    int fd = open(argv[1], O_RDONLY | O_DIRECTORY);
    if (fd < 0) die("open mountpoint");

    size_t bsz = sizeof(struct xfs_bulkstat_req)
               + (size_t)BULKSTAT_REQ * sizeof(struct xfs_bulkstat);
    struct xfs_bulkstat_req *bs = calloc(1, bsz);
    if (!bs) die("calloc bulkstat");
    bs->hdr.ino    = 0;              
    bs->hdr.flags  = 0;              
    bs->hdr.icount = BULKSTAT_REQ;  

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

    size_t isz = sizeof(struct xfs_inumbers_req)
               + (size_t)INUMBERS_REQ * sizeof(struct xfs_inumbers);
    struct xfs_inumbers_req *in = calloc(1, isz);
    if (!in) die("calloc inumbers");
    in->hdr.ino    = 0;              
    in->hdr.flags  = 0;
    in->hdr.icount = INUMBERS_REQ;   

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
