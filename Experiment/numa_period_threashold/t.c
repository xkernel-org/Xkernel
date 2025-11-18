#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <pthread.h>
#include <sys/mman.h>

/*
record the original and change:
echo 100  | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_delay_ms
echo 50   | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_period_min_ms
echo 1000 | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_period_max_ms
echo 512  | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_size_mb

original:
echo 1000  | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_delay_ms
echo 1000   | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_period_min_ms
echo 60000 | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_period_max_ms
echo 256  | sudo tee /sys/kernel/debug/sched/numa_balancing/scan_size_mb

compile:
gcc -O2 t.c -o t

make sure cpu0 and cpu15 are placed in different NUMA node
sudo ./t 16384 0 15 2

*/

static void bind_to_cpu(int cpu) {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (sched_setaffinity(0, sizeof(set), &set) != 0) {
        perror("sched_setaffinity");
        exit(1);
    }
}

struct thread_arg {
    char *buf;
    size_t size;
    int cpu_bind;
    int node_bind; // optional, might be superfluous
};

void *thr_fn(void *arg) {
    struct thread_arg *a = arg;
    char *buf = a->buf;
    size_t size = a->size;
    size_t step = 4096;
    bind_to_cpu(a->cpu_bind);
    while (1) {
        for (size_t i = 0; i < size; i += step) {
            buf[i]++;
        }
        // yield occasionally to let scheduler handle thread change
        sched_yield();
    }
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 5) {
        fprintf(stderr, "Usage: %s <size_mb> <cpu_node0> <cpu_node1> <threads>\n", argv[0]);
        return 1;
    }
    long size_mb = strtol(argv[1], NULL, 0);
    int cpu0 = atoi(argv[2]);
    int cpu1 = atoi(argv[3]);
    int threads = atoi(argv[4]);
    size_t size = size_mb * 1024UL * 1024UL;

    char *buf = mmap(NULL, size, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (buf == MAP_FAILED) {
        perror("mmap");
        return 1;
    }

    printf("First touch on CPU %d\n", cpu0);
    bind_to_cpu(cpu0);
    // First touch to allocate on node of cpu0
    for (size_t i = 0; i < size; i += 4096) {
        buf[i] = 1;
    }

    pthread_t *tids = calloc(threads, sizeof(pthread_t));
    struct thread_arg *args = calloc(threads, sizeof(struct thread_arg));

    for (int t = 0; t < threads; t++) {
        args[t].buf = buf;
        args[t].size = size;
        // Alternate binding across cpu0 and cpu1
        args[t].cpu_bind = ((t % 2) ? cpu1 : cpu0);
        args[t].node_bind = (t % 2) ? cpu1 : cpu0;
        pthread_create(&tids[t], NULL, thr_fn, &args[t]);
    }

    for (int t = 0; t < threads; t++) {
        pthread_join(tids[t], NULL);
    }

    return 0;
}
