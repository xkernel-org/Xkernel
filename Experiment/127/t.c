#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <numaif.h>
#include <sched.h>
#include <unistd.h>

#define SIZE   (512UL * 1024 * 1024)  // 512 MB
#define NODE_ALLOC 1
#define NODE_RUN   0

static char *buf;

/*
gcc -O2 -pthread t.c -lnuma -o t

sudo cat /sys/kernel/debug/sched/numa_balancing/scan_delay_ms
sudo cat /sys/kernel/debug/sched/numa_balancing/scan_period_min_ms
sudo cat /sys/kernel/debug/sched/numa_balancing/scan_period_max_ms
sudo cat /sys/kernel/debug/sched/numa_balancing/scan_size_mb
1000
1000
60000
256

echo 100 | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_delay_ms 
echo 100 | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_period_min_ms
echo 3000 | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_period_max_ms
echo 512 | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_size_mb

*/

void *worker(void *arg) {
    volatile char *p = buf;
    size_t i;
    while (1) {
        for (i = 0; i < SIZE; i += 4096) {
            p[i] = p[i] + 1;
        }
        // short sleep to allow scheduler preemption
        usleep(1000);
    }
    return NULL;
}

int main(void) {
    int ret;
    // bind thread to NODE_RUN
    cpu_set_t cpus;
    CPU_ZERO(&cpus);
    CPU_SET(0, &cpus);  // assume CPU 0 on node 0
    ret = sched_setaffinity(0, sizeof(cpus), &cpus);
    if (ret) perror("sched_setaffinity");

    // allocate buffer
    buf = malloc(SIZE);
    if (!buf) {
        perror("malloc");
        return 1;
    }

    // bind buffer to NODE_ALLOC
    ret = mbind(buf, SIZE, MPOL_BIND, (unsigned long[]){ NODE_ALLOC }, 1, 0);
    if (ret) perror("mbind");

    printf("Buffer allocated on node %d, running thread on node %d\n", NODE_ALLOC, NODE_RUN);

    pthread_t t;
    pthread_create(&t, NULL, worker, NULL);
    pthread_join(t, NULL);
    return 0;
}

