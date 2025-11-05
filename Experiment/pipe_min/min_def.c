// build: gcc -O2 -Wall min_def.c -o min_def

/*
# 需 root
# 把软配额调小，便于快速超额；记下原值以便恢复
orig_soft=$(cat /proc/sys/fs/pipe-user-pages-soft)
orig_hard=$(cat /proc/sys/fs/pipe-user-pages-hard)
sysctl -w fs.pipe-user-pages-soft=64   # 64页≈在默认16页/管道下，创建5个左右就会超
sysctl -w fs.pipe-user-pages-hard=0    # 先不启硬闸
# 查看默认单管道上限
sysctl fs.pipe-max-size
*/

#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>

int main() {
    // 先打开若干管道以快速超额
    int p[2];
    for (int i = 0; i < 8; i++) {
        if (pipe(p) == -1) { perror("pipe"); return 1; }
    }
    // 再创建一个“受限状态下的新管道”
    if (pipe(p) == -1) { perror("pipe"); return 1; }
    int sz = fcntl(p[1], F_GETPIPE_SZ);
    if (sz == -1) { perror("F_GETPIPE_SZ"); return 1; }
    printf("new pipe capacity (bytes) = %d\n", sz);
    return 0;
}
