// iowq_create_normal.c
#define _GNU_SOURCE
#include <liburing.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>

static void die(const char *m){ perror(m); exit(1); }

int main(int argc, char **argv) {
    if (argc < 5) {
        fprintf(stderr, "Usage: %s <dir> <nfiles> <qdepth> <secs>\n", argv[0]);
        return 1;
    }
    const char *dir = argv[1];
    int nfiles = atoi(argv[2]);
    int qd = atoi(argv[3]);
    int secs = atoi(argv[4]);

    // 预生成文件名
    char **names = calloc(nfiles, sizeof(char*));
    for (int i = 0; i < nfiles; i++) {
        names[i] = malloc(512);
        snprintf(names[i], 512, "%s/f%06d", dir, i);
    }

    struct io_uring ring;
    struct io_uring_params p = {0};
    if (io_uring_queue_init_params(qd, &ring, &p) < 0) die("queue_init");

    // 填满队列：openat + IOSQE_ASYNC
    for (int i = 0; i < qd; i++) {
        struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
        io_uring_prep_openat(sqe, AT_FDCWD, names[i % nfiles], O_RDONLY, 0);
        sqe->flags |= IOSQE_ASYNC;
        sqe->user_data = i;
    }
    io_uring_submit(&ring);

    time_t end = time(NULL) + secs;
    unsigned long sub = qd, comp = 0;

    while (time(NULL) < end) {
        struct io_uring_cqe *cqe;
        if (!io_uring_wait_cqe(&ring, &cqe)) {
            int fd = cqe->res;
            if (fd >= 0) close(fd);
            io_uring_cqe_seen(&ring, cqe);
            comp++;

            struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
            if (sqe) {
                static unsigned idx=0; idx++;
                io_uring_prep_openat(sqe, AT_FDCWD, names[idx % nfiles], O_RDONLY, 0);
                sqe->flags |= IOSQE_ASYNC;
                sqe->user_data = idx;
                sub++;
            }
        }
        if ((sub - comp) < qd/2) io_uring_submit(&ring);
    }

    io_uring_queue_exit(&ring);
    for (int i = 0; i < nfiles; i++) free(names[i]);
    free(names);
    fprintf(stderr, "done: submits=%lu comps=%lu\n", sub, comp);
    return 0;
}
