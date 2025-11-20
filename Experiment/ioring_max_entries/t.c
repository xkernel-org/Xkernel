// gcc -O2 -Wall t.c -luring -o t
#define _GNU_SOURCE
#include <liburing.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>

static volatile int running = 1;
static void on_sigint(int sig){ (void)sig; running = 0; }

static unsigned long get_sleep_us(void) {
    const char *e = getenv("CLAMP_SLEEP_US");
    return e ? strtoul(e, NULL, 10) : 10000; 
}

int main(void) {
    signal(SIGINT, on_sigint);
    unsigned long i = 0;
    unsigned long sleep_us = get_sleep_us();

    while (running) {
        struct io_uring ring;
        struct io_uring_params p;
        memset(&p, 0, sizeof(p));

        p.flags = IORING_SETUP_CLAMP | IORING_SETUP_CQSIZE;
        p.cq_entries = 1u << 20; 
        unsigned req = 1u << 20; 

        int ret = io_uring_queue_init_params(req, &ring, &p);
        if (ret) {
            fprintf(stderr, "init failed: %d\n", ret);
            usleep(1000);
            continue;
        }

        if ((++i % 1000ul) == 0)
            printf("[loop=%lu] actual sq=%u cq=%u flags=0x%x\n",
                   i, p.sq_entries, p.cq_entries, p.flags);

        io_uring_queue_exit(&ring);

        if (sleep_us) usleep(sleep_us);
        sched_yield();
    }
    return 0;
}
