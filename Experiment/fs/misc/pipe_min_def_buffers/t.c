// gcc -O2 -Wall t.c -o t

/*
orig_soft=$(cat /proc/sys/fs/pipe-user-pages-soft)
orig_hard=$(cat /proc/sys/fs/pipe-user-pages-hard)

sysctl -w fs.pipe-user-pages-soft=64   
sysctl -w fs.pipe-user-pages-hard=0    
sysctl fs.pipe-max-size
*/

#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>

int main() {
    int p[2];
    for (int i = 0; i < 8; i++) {
        if (pipe(p) == -1) { perror("pipe"); return 1; }
    }
    if (pipe(p) == -1) { perror("pipe"); return 1; }
    int sz = fcntl(p[1], F_GETPIPE_SZ);
    if (sz == -1) { perror("F_GETPIPE_SZ"); return 1; }
    printf("new pipe capacity (bytes) = %d\n", sz);
    return 0;
}
