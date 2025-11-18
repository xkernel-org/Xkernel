#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <sys/mman.h>
#include <sys/wait.h>

// 假设 Node 0 包含 CPU 0, Node 1 包含 CPU 1
#define CPU_NODE_0 0
#define CPU_NODE_1 1

#define MEM_SIZE (1 * 1024 * 1024 * 1024) // 1 GB

// 将进程绑定到指定CPU
void pin_to_cpu(int cpu) {
    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(cpu, &mask);
    if (sched_setaffinity(0, sizeof(mask), &mask) < 0) {
        perror("sched_setaffinity");
        exit(1);
    }
}

// 访问内存的函数
void access_memory(char *mem) {
    for (int i = 0; i < 100; i++) {
        for (int j = 0; j < MEM_SIZE; j += 4096) {
            mem[j] = (char)(i + j); // 写入
        }
        usleep(10000); // 10ms
    }
}

int main() {
    // 1. 分配共享内存
    char *shared_mem = mmap(NULL, MEM_SIZE, PROT_READ | PROT_WRITE,
                            MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (shared_mem == MAP_FAILED) {
        perror("mmap");
        return 1;
    }

    // 2. P1 (父进程) 绑定到 Node 0 并初始化内存
    pin_to_cpu(CPU_NODE_0);
    printf("P1 (PID %d) on CPU %d, initializing memory on Node 0.\n", getpid(), sched_getcpu());
    access_memory(shared_mem); // 内存被分配在 Node 0

    // 3. 创建 P2
    pid_t p2_pid = fork();
    if (p2_pid == 0) {
        // P2 (子进程)
        pin_to_cpu(CPU_NODE_1);
        printf("P2 (PID %d) on CPU %d, accessing memory from Node 1.\n", getpid(), sched_getcpu());
        sleep(2); // 等待P1成熟，并确保P3在P2之后运行
        access_memory(shared_mem); // 触发第一次 NUMA fault (在 Condition 5 中断)
        exit(0);
    }

    // 4. 创建 P3
    pid_t p3_pid = fork();
    if (p3_pid == 0) {
        // P3 (子进程)
        pin_to_cpu(CPU_NODE_1);
        printf("P3 (PID %d) on CPU %d, accessing memory from Node 1.\n", getpid(), sched_getcpu());
        sleep(4); // 确保在P2访问之后再访问
        access_memory(shared_mem); // 触发第二次 NUMA fault (到达最终 return)
        exit(0);
    }

    // P1 等待子进程结束
    waitpid(p2_pid, NULL, 0);
    waitpid(p3_pid, NULL, 0);

    munmap(shared_mem, MEM_SIZE);
    return 0;
}

// 编译：gcc -o t t.c -pthread
