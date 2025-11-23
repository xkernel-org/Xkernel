// gcc -O2 -Wall -pthread t.c -luring -o t
#define _GNU_SOURCE
#include <liburing.h>
#include <sys/eventfd.h>
#include <pthread.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>

static int nb(int fd){int f=fcntl(fd,F_GETFL,0); return fcntl(fd,F_SETFL,f|O_NONBLOCK);}

static int efd;

static void* toggler(void*){
    uint64_t one=1, val;
    while (1) {
        write(efd, &one, 8);   
        read(efd, &val, 8);    
    }
    return NULL;
}

int main(void){
    struct io_uring ring;
    struct io_uring_cqe *cqe;
    uint64_t val;

    efd = eventfd(0, EFD_NONBLOCK|EFD_CLOEXEC);
    nb(efd);

    pthread_t th; pthread_create(&th, NULL, toggler, NULL);

    io_uring_queue_init(64, &ring, 0);

    for (int i=0; i<100000; i++) {
        struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
        io_uring_prep_read(sqe, efd, &val, 8, 0);
        io_uring_submit(&ring);

        if (!io_uring_wait_cqe(&ring, &cqe)) {
            io_uring_cqe_seen(&ring, cqe);
        }
    }

    io_uring_queue_exit(&ring);
    close(efd);
    return 0;
}
