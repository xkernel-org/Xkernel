// gcc -O2 -Wall t.c -luring -o t
// ./t --qd=8192 --batch=4096
#define _GNU_SOURCE
#include <liburing.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>

int main(int argc, char **argv) {
    int qd = 8192, batch = 4096;  
    const char *path = "/tmp/io_ref.bin";
    for (int i = 1; i < argc; i++) {
        if (!strncmp(argv[i], "--qd=", 5)) qd = atoi(argv[i]+5);
        else if (!strncmp(argv[i], "--batch=", 8)) batch = atoi(argv[i]+8);
    }

    int fd = open(path, O_RDWR|O_CREAT, 0644);
    if (fd < 0) { perror("open"); return 1; }
    if (ftruncate(fd, 1<<20) < 0) { perror("ftruncate"); return 1; } 

    struct io_uring ring;
    struct io_uring_params p = {0};
    if (io_uring_queue_init_params(qd, &ring, &p) < 0) { perror("io_uring_queue_init_params"); return 2; }

    for (unsigned long long it = 0; ; it++) {
        for (int i = 0; i < batch; i++) {
            struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
            if (!sqe) { 
                int r = io_uring_submit(&ring);
                if (r < 0) { perror("io_uring_submit"); return 3; }
                i--; continue;
            }
            off_t off = (off_t)((i & 0x3FF) * 4096);   
            io_uring_prep_fadvise(sqe, fd, off, 4096, POSIX_FADV_DONTNEED);
            sqe->flags |= IOSQE_ASYNC;                 
            sqe->user_data = (it<<32) | (unsigned)i;
        }
        int ret = io_uring_submit(&ring);
        if (ret < 0) { perror("io_uring_submit"); break; }

        for (int i = 0; i < batch; i++) {
            struct io_uring_cqe *cqe;
            if (io_uring_wait_cqe(&ring, &cqe) < 0) { perror("wait_cqe"); return 4; }
            io_uring_cqe_seen(&ring, cqe);
        }
    }

    io_uring_queue_exit(&ring);
    close(fd);
    return 0;
}
