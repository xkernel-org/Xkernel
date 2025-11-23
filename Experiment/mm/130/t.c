// gcc -O2 -pthread -o t t.c
#define _GNU_SOURCE
#include <fcntl.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>

#ifndef DIRNAME
#define DIRNAME "./streamdir"
#endif

static size_t file_mb_initial = 256;   
static size_t file_count       = 4;    
static size_t grow_mb_per_epoch= 128;  
static size_t read_chunk_mb    = 4;    
static int    threads          = 2;   

static volatile int ballast_on = 1;
static char *ballast = NULL;
static size_t ballast_target_mb = 64;   
static size_t ballast_cap_mb    = 1024; 

static long read_cgroup_bytes(const char *name) {
    char path[256];
    snprintf(path, sizeof(path), "/sys/fs/cgroup/%s", name);
    FILE *f = fopen(path, "r");
    if(!f) return -1;
    long v = -1;
    if (fscanf(f, "%ld", &v) != 1) v = -1;
    fclose(f);
    return v; // bytes
}

static void adjust_ballast() {
    long high = read_cgroup_bytes("memory.high");
    long max  = read_cgroup_bytes("memory.max");
    long cur  = read_cgroup_bytes("memory.current");
    if (high <= 0 || max <= 0 || cur < 0) return;

    long target = (long)(high * 0.95);
    if (target > max - (64L<<20)) target = max - (64L<<20); 
    if (target < 0) target = high;

    long need = target - cur;
    if (need > (16L<<20) && ballast_target_mb < ballast_cap_mb) {
        ballast_target_mb += 16; 
    } else if (need < -(32L<<20) && ballast_target_mb > 16) {
        ballast_target_mb -= 16; 
    }

    size_t want = ballast_target_mb * (1UL<<20);
    static size_t have = 0;
    if (want > have) {
        char *p = realloc(ballast, want);
        if (p) {
            ballast = p;
            memset(ballast + have, 0x5A, want - have);
            have = want;
        }
    } else if (want + (16UL<<20) < have) {
        have -= (16UL<<20);
        ballast = realloc(ballast, have);
    }
}

static void *ballast_thread(void *arg) {
    (void)arg;
    while (ballast_on) {
        adjust_ballast();
        usleep(200*1000);
    }
    return NULL;
}

static int ensure_dir(const char *d) {
    struct stat st;
    if (stat(d, &st) == 0) {
        if (S_ISDIR(st.st_mode)) return 0;
        errno = ENOTDIR; return -1;
    }
    if (mkdir(d, 0755) == 0) return 0;
    return -1;
}

static int grow_file(const char *path, size_t new_mb) {
    int fd = open(path, O_RDWR | O_CREAT, 0644);
    if (fd < 0) return -1;
    off_t want = (off_t)new_mb * 1024 * 1024;
    if (ftruncate(fd, want) < 0) { close(fd); return -1; }
    size_t poke = 4*1024*1024;
    void *m = mmap(NULL, poke, PROT_READ|PROT_WRITE, MAP_SHARED, fd, want - poke);
    if (m != MAP_FAILED) { memset(m, 0xA5, poke); munmap(m, poke); }
    close(fd);
    return 0;
}

typedef struct {
    char **files;
    size_t nfiles;
    size_t from_mb;
    size_t to_mb;
} reader_args_t;

static void *reader_worker(void *arg) {
    reader_args_t *a = (reader_args_t*)arg;
    size_t chunk = read_chunk_mb * 1024UL * 1024UL;
    void *buf = malloc(chunk);
    if (!buf) return NULL;

    for (size_t i = 0; i < a->nfiles; i++) {
        const char *path = a->files[i];
        int fd = open(path, O_RDONLY);
        if (fd < 0) continue;

        off_t off = (off_t)a->from_mb * 1024 * 1024;
        off_t end = (off_t)a->to_mb   * 1024 * 1024;
        if (end <= off) { close(fd); continue; }

        while (off < end) {
            size_t to_read = (end - off) < (off_t)chunk ? (size_t)(end - off) : chunk;
            ssize_t r = pread(fd, buf, to_read, off);
            if (r <= 0) break;
            off += r;
        }
        close(fd);
    }
    free(buf);
    return NULL;
}

int main(int argc, char **argv) {
    if (argc >= 2) file_count = strtoul(argv[1], NULL, 0);
    if (argc >= 3) file_mb_initial = strtoul(argv[2], NULL, 0);
    if (argc >= 4) grow_mb_per_epoch = strtoul(argv[3], NULL, 0);

    if (ensure_dir(DIRNAME) < 0) {
        perror("mkdir streamdir"); return 1;
    }

    char **files = calloc(file_count, sizeof(char*));
    for (size_t i = 0; i < file_count; i++) {
        files[i] = malloc(256);
        snprintf(files[i], 256, "%s/file_%zu.dat", DIRNAME, i);
        grow_file(files[i], file_mb_initial);
    }

    pthread_t th;
    pthread_create(&th, NULL, ballast_thread, NULL);

    size_t cur_mb = file_mb_initial;
    size_t epoch = 0;

    while (1) {
        epoch++;
        size_t new_mb = cur_mb + grow_mb_per_epoch;

        for (size_t i = 0; i < file_count; i++) {
            if (grow_file(files[i], new_mb) < 0) {
                fprintf(stderr, "grow_file failed: %s\n", files[i]);
            }
        }

        reader_args_t args = {
            .files   = files,
            .nfiles  = file_count,
            .from_mb = cur_mb,
            .to_mb   = new_mb
        };
        pthread_t *workers = calloc(threads, sizeof(pthread_t));
        for (int t = 0; t < threads; t++)
            pthread_create(&workers[t], NULL, reader_worker, &args);
        for (int t = 0; t < threads; t++)
            pthread_join(workers[t], NULL);
        free(workers);

        cur_mb = new_mb;

        long cur = read_cgroup_bytes("memory.current");
        long high= read_cgroup_bytes("memory.high");
        long mx  = read_cgroup_bytes("memory.max");
        fprintf(stderr, "[epoch %zu] files=%zu each=%zuMB  mem.cur=%.1fMB high=%.1fMB max=%.1fMB ballast=%zuMB\n",
            epoch, file_count, cur_mb, cur/1048576.0, high/1048576.0, mx/1048576.0, ballast_target_mb);

        usleep(200*1000);
    }

    ballast_on = 0; pthread_join(th, NULL);
    return 0;
}
