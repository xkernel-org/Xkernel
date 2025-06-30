#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <sched.h>

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <cpu> <sleep_usec>\n", argv[0]);
        return 1;
    }

    int cpu = atoi(argv[1]);
    long sleep_usec = atol(argv[2]);

    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(cpu, &mask);
    if (sched_setaffinity(0, sizeof(mask), &mask) == -1) {
        perror("sched_setaffinity");
        return 1;
    }

    printf("Pinned to CPU %d, sleeping for %ld usec in a loop.\n", cpu, sleep_usec);

    struct timespec req = {
        .tv_sec = 0,
        .tv_nsec = sleep_usec * 1000
    };

    while (1) {
        nanosleep(&req, NULL);
    }

    return 0;
}
