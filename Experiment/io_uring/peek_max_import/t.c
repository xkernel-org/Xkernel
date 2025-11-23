#define _GNU_SOURCE
#include <liburing.h>
#include <arpa/inet.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

#ifndef IORING_RECVSEND_BUNDLE
#define IORING_RECVSEND_BUNDLE (1U << 4)
#endif
#ifndef IORING_FEAT_RECVSEND_BUNDLE
#define IORING_FEAT_RECVSEND_BUNDLE (1U << 14)
#endif
#ifndef IORING_CQE_BUFFER_SHIFT
#define IORING_CQE_BUFFER_SHIFT 16
#endif

#define QD         64
#define PORT       12345
#define BGID       7
#define BR_ENTRIES 4096      
#define BUF_SZ     2048
#define WANT_SEGS  300       

static int listen_tcp(void)
{
    int s = socket(AF_INET, SOCK_STREAM, 0);
    int one = 1;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(PORT),
        .sin_addr   = { htonl(INADDR_LOOPBACK) }
    };
    if (bind(s, (struct sockaddr*)&addr, sizeof(addr)) < 0) { perror("bind"); exit(1); }
    if (listen(s, 128) < 0) { perror("listen"); exit(1); }
    return s;
}

int main(void) {
    struct io_uring ring;
    struct io_uring_params p = {0};

    int ls = listen_tcp();
    int cs = accept(ls, NULL, NULL);
    if (cs < 0) { perror("accept"); return 1; }

    if (io_uring_queue_init_params(QD, &ring, &p) < 0) {
        perror("io_uring_queue_init_params");
        return 1;
    }
    if (!(p.features & IORING_FEAT_RECVSEND_BUNDLE)) {
        fprintf(stderr, "Kernel lacks IORING_FEAT_RECVSEND_BUNDLE\n");
        return 1;
    }

    int err = 0;
    struct io_uring_buf_ring *br =
        io_uring_setup_buf_ring(&ring, BR_ENTRIES, BGID, 0, &err);
    if (!br) { errno = -err; perror("io_uring_setup_buf_ring"); return 1; }

    int br_mask = io_uring_buf_ring_mask(BR_ENTRIES);
    io_uring_buf_ring_init(br);

    void *pool = NULL;
    if (posix_memalign(&pool, 4096, (size_t)BR_ENTRIES * BUF_SZ)) {
        perror("posix_memalign"); return 1;
    }
    for (unsigned i = 0; i < BR_ENTRIES; i++) {
        void *ptr = (char *)pool + (size_t)i * BUF_SZ;
        io_uring_buf_ring_add(br, ptr, BUF_SZ, i, br_mask, 0);
    }
    io_uring_buf_ring_advance(br, BR_ENTRIES);

    size_t want_bytes = (size_t)WANT_SEGS * BUF_SZ;         
    struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    io_uring_prep_recv(sqe, cs, NULL, want_bytes, 0);      
    sqe->flags     |= IOSQE_BUFFER_SELECT;
    sqe->buf_group  = BGID;
    sqe->ioprio    |= IORING_RECVSEND_BUNDLE;

    if (io_uring_submit(&ring) < 0) { perror("io_uring_submit"); return 1; }

    struct io_uring_cqe *cqe;
    int ret = io_uring_wait_cqe(&ring, &cqe);
    if (ret < 0) { fprintf(stderr, "wait_cqe=%s\n", strerror(-ret)); return 1; }

    int res = cqe->res;
    unsigned first_bid = (cqe->flags & IORING_CQE_F_BUFFER) ? (cqe->flags >> IORING_CQE_BUFFER_SHIFT) : 0;
    printf("recv bundle: res=%d bytes, first_bid=%u\n", res, first_bid);

    unsigned used = (res + BUF_SZ - 1) / BUF_SZ;
    printf("approx segments used ~= %u (want=%zu bytes, buf=%d)\n", used, want_bytes, BUF_SZ);
    io_uring_buf_ring_cq_advance(&ring, br, used);
    io_uring_cqe_seen(&ring, cqe);

    close(cs); close(ls);
    io_uring_free_buf_ring(&ring, br, BR_ENTRIES, BGID);
    free(pool);
    io_uring_queue_exit(&ring);
    return 0;
}
