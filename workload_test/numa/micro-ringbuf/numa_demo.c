#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sched.h>
#include <time.h>

// Define a large buffer size (e.g., 2GB)
#define BUFFER_SIZE (20 * 1024 * 1024 * 1024L)

// Global flag to signal threads to stop
volatile int keep_running = 1;

// A struct to hold thread arguments
struct thread_args {
    char *buffer;
    int cpu;
};

// The function that each thread will execute
void *thread_func(void *arg) {
    struct thread_args *args = (struct thread_args *)arg;
    cpu_set_t cpuset;
    long long completed_passes = 0; // Counter for throughput calculation

    CPU_ZERO(&cpuset);
    CPU_SET(args->cpu, &cpuset);

    if (pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset) != 0) {
        perror("pthread_setaffinity_np");
        return NULL;
    }

    printf("Thread started on CPU %d\n", args->cpu);

    // Keep working as long as the flag is set
    for (long j = 0; j < BUFFER_SIZE; ++j) {
        args->buffer[j]++;
    }

    return NULL;
}

int main() {
    pthread_t thread1, thread2;
    struct thread_args args1, args2;
    char *buffer;

    buffer = (char *)malloc(BUFFER_SIZE);
    if (!buffer) {
        perror("malloc");
        return 1;
    }
    memset(buffer, 0, BUFFER_SIZE);

    args1.buffer = buffer;
    args1.cpu = 0;

    args2.buffer = buffer;
    args2.cpu = 1;

    if (pthread_create(&thread1, NULL, thread_func, &args1) != 0) {
        perror("pthread_create");
        return 1;
    }
    if (pthread_create(&thread2, NULL, thread_func, &args2) != 0) {
        perror("pthread_create");
        return 1;
    }

    printf("Waiting for threads to join...\n");
    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);

    free(buffer);

    return 0;
}
