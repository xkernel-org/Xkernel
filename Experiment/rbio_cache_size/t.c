// build: gcc -O2 -Wall hotstripe.c -o hotstripe
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <time.h>
#define STRIPE (64*1024)
#define BS 4096
int main(int argc, char **argv){
    if (argc < 3){ fprintf(stderr,"usage: %s <file> <seconds>\n", argv[0]); return 1; }
    int secs = atoi(argv[2]);
    void *buf; if (posix_memalign(&buf, 4096, BS)) return 2;
    memset(buf, 0xab, BS);
    int fd = open(argv[1], O_CREAT|O_WRONLY|O_DIRECT|O_DSYNC, 0644);
    if (fd < 0){ perror("open"); return 3; }
    uint64_t off = 0; time_t t0=time(NULL);
    while (time(NULL)-t0 < secs){
        if (pwrite(fd, buf, BS, off) != BS){ perror("pwrite"); return 4; }
        fsync(fd);
        off += BS; if (off >= STRIPE) off = 0;
    }
    close(fd); free(buf); return 0;
}
