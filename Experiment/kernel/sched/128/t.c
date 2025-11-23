// gcc -o t t.c -pthread
// Hard to trigger

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <sys/mman.h>
#include <sys/wait.h>

#define CPU_NODE_0 0
#define CPU_NODE_1 1

#define MEM_SIZE (1 * 1024 * 1024 * 1024) // 1 GB

void pin_to_cpu(int cpu) {
    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(cpu, &mask);
    if (sched_setaffinity(0, sizeof(mask), &mask) < 0) {
        perror("sched_setaffinity");
        exit(1);
    }
}

void access_memory(char *mem) {
    for (int i = 0; i < 100; i++) {
        for (int j = 0; j < MEM_SIZE; j += 4096) {
            mem[j] = (char)(i + j); 
        }
        usleep(10000); 
    }
}

int main() {
    char *shared_mem = mmap(NULL, MEM_SIZE, PROT_READ | PROT_WRITE,
                            MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (shared_mem == MAP_FAILED) {
        perror("mmap");
        return 1;
    }

    pin_to_cpu(CPU_NODE_0);
    printf("P1 (PID %d) on CPU %d, initializing memory on Node 0.\n", getpid(), sched_getcpu());
    access_memory(shared_mem); 

    pid_t p2_pid = fork();
    if (p2_pid == 0) {
        pin_to_cpu(CPU_NODE_1);
        printf("P2 (PID %d) on CPU %d, accessing memory from Node 1.\n", getpid(), sched_getcpu());
        sleep(2); 
        access_memory(shared_mem); 
        exit(0);
    }

    pid_t p3_pid = fork();
    if (p3_pid == 0) {
        pin_to_cpu(CPU_NODE_1);
        printf("P3 (PID %d) on CPU %d, accessing memory from Node 1.\n", getpid(), sched_getcpu());
        sleep(4); 
        access_memory(shared_mem); 
        exit(0);
    }

    waitpid(p2_pid, NULL, 0);
    waitpid(p3_pid, NULL, 0);

    munmap(shared_mem, MEM_SIZE);
    return 0;
}

