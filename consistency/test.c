#include <stdio.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/mman.h>
#include <string.h>
#include <sched.h>
#include <errno.h>

#define NUM_CALLS 50000
#define NUM_THREADS 8

void* call_getpid(void* arg) {
    int calls = NUM_CALLS;
    for (int i = 0; i < calls; i++) {
        void *addr = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);
        if (addr != MAP_FAILED) munmap(addr, 4096);
    }
    return NULL;
}

int main() {
    pthread_t threads[NUM_THREADS];

    for (int i = 0; i < NUM_THREADS; i++) {
        if (pthread_create(&threads[i], NULL, call_getpid, NULL) != 0) {
            perror("pthread_create failed");
            return 1;
        }
        
        char thread_name[16];
        snprintf(thread_name, sizeof(thread_name), "test %d", i);
        pthread_setname_np(threads[i], thread_name);
    }

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    return 0;
}