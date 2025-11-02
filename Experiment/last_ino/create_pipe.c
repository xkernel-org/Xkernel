// trigger_last_ino_batch.c
#define _GNU_SOURCE
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>

// compile: gcc -O2 -Wall create_pipe.c -o create_pipe

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atoll(argv[1]) : 1000000; // default
    int fds[2];
    for (long i = 0; i < iters; i++) {
        if (pipe2(fds, O_CLOEXEC | O_NONBLOCK) == -1) {
            perror("pipe2");
            return 1;
        }
        close(fds[0]);
        close(fds[1]);
    }
    return 0;
}
