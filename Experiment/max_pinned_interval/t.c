// burn.c
#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>

int main() {
    volatile uint64_t x = 0;
    for (;;) { x += 1; if (!(x & ((1u<<20)-1))) sched_yield(); }
    return 0;
}

/*
taskset -c 0 ./t &    # P1 在 CPU0 
taskset -c 0 ./t &    # P2 仍在 CPU
sleep 30
*/