#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <unistd.h>

#define MATRIX_SIZE 32

// Multiply two matrices of fixed size
void matrix_multiply(volatile double A[MATRIX_SIZE][MATRIX_SIZE],
                     volatile double B[MATRIX_SIZE][MATRIX_SIZE],
                     volatile double C[MATRIX_SIZE][MATRIX_SIZE]) {
    for (int i = 0; i < MATRIX_SIZE; i++)
        for (int j = 0; j < MATRIX_SIZE; j++) {
            C[i][j] = 0.0;
            for (int k = 0; k < MATRIX_SIZE; k++)
                C[i][j] += A[i][k] * B[k][j];
        }
}

// Get current time in nanoseconds
uint64_t now_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s A B\n", argv[0]);
        return 1;
    }

    uint64_t busy_time = strtoull(argv[1], NULL, 10);
    uint64_t sleep_time = strtoull(argv[2], NULL, 10);

    // Allocate and initialize matrices
    static volatile double A[MATRIX_SIZE][MATRIX_SIZE];
    static volatile double B[MATRIX_SIZE][MATRIX_SIZE];
    static volatile double C[MATRIX_SIZE][MATRIX_SIZE];
    for (int i = 0; i < MATRIX_SIZE; i++)
        for (int j = 0; j < MATRIX_SIZE; j++) {
            A[i][j] = 1.0;
            B[i][j] = 2.0;
        }

    struct timespec ts_sleep;
    ts_sleep.tv_sec = sleep_time / 1000000000ULL;
    ts_sleep.tv_nsec = sleep_time % 1000000000ULL;

    while (1) {
        uint64_t start = now_ns();
        while (now_ns() - start < busy_time) {
            matrix_multiply(A, B, C);
        }
        nanosleep(&ts_sleep, NULL);
    }

    return 0;
}
