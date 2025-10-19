#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdatomic.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <pthread.h>
#include <time.h>
#include <sched.h>
#include <sys/mman.h>
#include <numa.h>
#include <numaif.h>

#ifndef MAP_ANONYMOUS
#  define MAP_ANONYMOUS MAP_ANON
#endif

// gcc -O2 -pthread benchmark.c -o benchmark -lnuma

// ---------------------- Configuration and Statistics ----------------------
typedef struct {
    long pages;                 // Number of 4KiB pages
    int duration_sec;           // Runtime duration in seconds
    int workers;                // Number of query threads
    int migrates;               // Number of migration threads
    int src_node;               // Initial placement node
    int dst_node;               // Destination (query) node
    int migrate_batch;          // Max pages to migrate per call (user-level batch)
    int migrate_interval_ms;    // Throttling interval between migrations in ms
    double hot_frac;            // Hot window fraction (0,1]
    double hot_prob;            // Worker hit probability for the hot window
    int hot_rotate_sec;         // Hot window rotation period (seconds), 0=no rotation
    int verify_residency;       // Print page residency distribution at start/end
    int use_move_all;           // Use MPOL_MF_MOVE_ALL (requires CAP_SYS_NICE)

    // === Migration Strategy Enhancements ===
    int rotate_step_full;       // Rotation step size: 1=full window width, 0=1/4 window
    int drain_per_window;       // Max "drain" rounds per window (0=disable)
    int only_src;               // Only migrate pages from the src node (reduce wasted calls)
    int restat_before_move;     // Re-stat the batch for filtering before submitting the migration

    // === Observability ===
    int qps_sample_ms;          // QPS sampling period in ms (0=disable, 10 recommended)
    int probe_ops;              // Probe: number of accesses in one "query" (0=disable, 2000 recommended)
    int probe_period_ms;        // Probe: interval between two probes in ms (50-100 recommended)
} Config;

typedef struct { atomic_ulong ops; } WorkerStats;

typedef struct {
    atomic_ulong calls;
    atomic_ulong pages_succ;
    atomic_ulong pages_fail;
    atomic_ulong us_sum;
} MigStats;

static Config CFG = {
    .pages = 65536 * 4 * 4,     // 256 MiB * 4 * 4 = 4 GiB (default)
    .duration_sec = 30,
    .workers = 24,
    .migrates = 4,
    .src_node = 1,
    .dst_node = 0,
    .migrate_batch = 256,
    .migrate_interval_ms = 10,
    .hot_frac = 0.10,
    .hot_prob = 0.80,
    .hot_rotate_sec = 0,
    .verify_residency = 1,
    .use_move_all = 0,
    .rotate_step_full = 0,
    .drain_per_window = 0,
    .only_src = 0,
    .restat_before_move = 0,
    .qps_sample_ms = 10,
    .probe_ops = 0,
    .probe_period_ms = 50,
};

static size_t PAGE_SZ;
static void *g_base = NULL;       // Mapped base address
static void **g_page_ptrs = NULL; // Array of virtual address pointers for each page
static atomic_long HOT_BASE = 0;  // Start of the hot window (page index)
static volatile int STOP = 0;

static WorkerStats WSTAT = {0};
static MigStats MSTAT = {0};

// ---- QPS Window Samples ----
static double *QPS_SAMPLES = NULL;
static int QPS_CAP = 0, QPS_N = 0;
static pthread_mutex_t QPS_LOCK = PTHREAD_MUTEX_INITIALIZER;

// ---- Probe micro-batch latency samples (microseconds) ----
static double *PROBE_LAT = NULL;
static int PROBE_CAP = 0, PROBE_N = 0;
static pthread_mutex_t PROBE_LOCK = PTHREAD_MUTEX_INITIALIZER;

// ---------------------- Simple RNG ----------------------
static inline uint64_t rng_next(uint64_t *s) {
    *s = *s * 2862933555777941757ULL + 3037000493ULL;
    return *s;
}
static inline double rng_uniform(uint64_t *s) {
    return (rng_next(s) >> 11) * (1.0/9007199254740992.0); // [0,1)
}

// ---------------------- CPU Pinning Utility ----------------------
static int pin_to_cpu(int cpu) {
    cpu_set_t set; CPU_ZERO(&set); CPU_SET(cpu, &set);
    return sched_setaffinity(0, sizeof(set), &set);
}

static int pin_to_node_roundrobin(int node, int slot) {
    if (numa_available() < 0) return 0;
    struct bitmask *bm = numa_allocate_cpumask();
    if (!bm) return -1;
    numa_node_to_cpus(node, bm);
    int ncpu = 0;
    for (unsigned int i = 0; i < bm->size; i++) if (numa_bitmask_isbitset(bm, i)) ncpu++;
    if (ncpu == 0) { numa_free_cpumask(bm); return -1; }
    int pick = slot % ncpu, seen = 0, target = -1;
    for (unsigned int i = 0; i < bm->size; i++) {
        if (numa_bitmask_isbitset(bm, i)) {
            if (seen == pick) { target = i; break; }
            seen++;
        }
    }
    numa_free_cpumask(bm);
    if (target >= 0) return pin_to_cpu(target);
    return -1;
}

// ---------------------- Time & Quantile Utilities ----------------------
static inline uint64_t nsec_now(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec*1000000000ull + ts.tv_nsec;
}
static int dblcmp(const void *a, const void *b){
    double x = *(const double*)a, y = *(const double*)b;
    return (x<y)?-1:((x>y)?1:0);
}
static double pct_val(double *a, int n, double p){ // 0<=p<=1
    if (n<=0) return 0.0;
    double r = p*(n-1);
    int i = (int)r; double frac = r - i;
    if (i+1 < n) return a[i]*(1.0-frac) + a[i+1]*frac;
    return a[n-1];
}

// ---------------------- Residency Query and Print ----------------------
static void residency_summary(const int *status, long n, int *counts, int maxnode) {
    memset(counts, 0, sizeof(int)*(maxnode+1));
    for (long i = 0; i < n; i++) {
        int v = status[i];
        if (v >= 0 && v <= maxnode) counts[v]++;
    }
}

static void print_residency_all(const char *tag) {
    int maxnode = numa_max_node();
    int *status = (int*)calloc(CFG.pages, sizeof(int));
    if (!status) return;
    int rc = move_pages(0, CFG.pages, g_page_ptrs, NULL, status, 0); // Query
    if (rc < 0) { perror("move_pages(stat)"); free(status); return; }
    int *cnt = (int*)calloc(maxnode+1, sizeof(int));
    residency_summary(status, CFG.pages, cnt, maxnode);
    fprintf(stderr, "[%s] residency:", tag);
    for (int i = 0; i <= maxnode; i++) fprintf(stderr, " node%d=%d", i, cnt[i]);
    fprintf(stderr, "\n");
    free(cnt); free(status);
}

// ---------------------- Initial Placement (first touch on src) ----------------------
typedef struct { long begin, end; int node; } InitArg;

static void *init_touch_thread(void *arg_) {
    InitArg *arg = (InitArg*)arg_;
    pin_to_node_roundrobin(arg->node, 0);
    for (long i = arg->begin; i < arg->end; i++) {
        volatile uint64_t *p = (volatile uint64_t*)g_page_ptrs[i];
        *p = (uint64_t)i; // First write, ensures page is allocated on src
    }
    return NULL;
}

static void initial_place_on_src(void) {
    InitArg a = { .begin = 0, .end = CFG.pages, .node = CFG.src_node };
    pthread_t th; pthread_create(&th, NULL, init_touch_thread, &a);
    pthread_join(th, NULL);
}

// ---------------------- Hotspot Selection ----------------------
static inline long pick_hot_index(uint64_t *seed, long total, double hot_frac, double hot_prob, long hot_base) {
    long hot_sz = (long)(total * hot_frac);
    if (hot_sz <= 0) hot_sz = 1;
    if (rng_uniform(seed) < hot_prob) {
        long off = (long)(rng_uniform(seed) * hot_sz);
        return (hot_base + off) % total;
    } else {
        while (1) {
            long idx = (long)(rng_uniform(seed) * total);
            long rel = (idx - hot_base + total) % total;
            if (rel >= hot_sz) return idx;
        }
    }
}

// ---------------------- Worker Thread ----------------------
static void *worker_thread(void *arg_) {
    long tidx = (long)(intptr_t)arg_;
    pin_to_node_roundrobin(CFG.dst_node, (int)tidx);
    uint64_t seed = 0x9e3779b97f4a7c15ULL ^ (uint64_t)pthread_self();
    while (!STOP) {
        long hb = atomic_load_explicit(&HOT_BASE, memory_order_relaxed);
        long idx = pick_hot_index(&seed, CFG.pages, CFG.hot_frac, CFG.hot_prob, hb);
        volatile uint64_t *p = (volatile uint64_t*)g_page_ptrs[idx];
        if((seed & 0x3) % 10 < 2) {
            *p += 1;
        } else {
            volatile uint64_t v = *p;
            v = v + 2;
        }
        // uint64_t v = *p; *p = v + 1;
        atomic_fetch_add_explicit(&WSTAT.ops, 1, memory_order_relaxed);
    }
    return NULL;
}

// ---------------------- Hotspot Rotation ----------------------
static void *hot_rotator_thread(void *arg_) {
    (void)arg_;
    if (CFG.hot_rotate_sec <= 0) return NULL;
    while (!STOP) {
        sleep(CFG.hot_rotate_sec);
        long base = atomic_load(&HOT_BASE);
        long step = (long)(CFG.pages * CFG.hot_frac);
        if (!CFG.rotate_step_full) step /= 4; // quarter mode
        if (step <= 0) step = 1;
        long next = (base + step) % CFG.pages;
        atomic_store(&HOT_BASE, next);
    }
    return NULL;
}

// ---------------------- Migrate Remote Hot Pages Only (supports only-src & restat) ----------------------
static int restat_filter(void **pages, int *nodes, int n,
                         int dst_node, int src_node, int only_src)
{
    if (n <= 0) return 0;
    int *st2 = (int*)malloc(sizeof(int)*n);
    if (!st2) return n; // Give up secondary filtering if memory is insufficient
    int rc = move_pages(0, n, pages, NULL, st2, 0); // Stat again
    if (rc < 0) { free(st2); return n; }

    int k = 0;
    for (int i = 0; i < n; i++) {
        int ok = only_src ? (st2[i] == src_node)
                          : (st2[i] >= 0 && st2[i] != dst_node);
        if (ok) {
            pages[k] = pages[i];
            nodes[k] = dst_node;
            k++;
        }
    }
    free(st2);
    return k;
}

static int collect_remote_hot(void **batch_pages, int *batch_nodes,
                              int maxwant, int dst_node, int src_node, int only_src)
{
    long hb = atomic_load_explicit(&HOT_BASE, memory_order_relaxed);
    long hot_sz = (long)(CFG.pages * CFG.hot_frac);
    if (hot_sz <= 0) hot_sz = 1;
    if (hot_sz > CFG.pages) hot_sz = CFG.pages;

    void **addrs = (void**)malloc(sizeof(void*) * hot_sz);
    int *status = (int*)malloc(sizeof(int) * hot_sz);
    if (!addrs || !status) { free(addrs); free(status); return 0; }

    for (long i = 0; i < hot_sz; i++) {
        long idx = (hb + i) % CFG.pages;
        addrs[i] = g_page_ptrs[idx];
    }

    int rc = move_pages(0, hot_sz, addrs, NULL, status, 0); // Query locations
    if (rc < 0) { perror("move_pages(stat)"); free(addrs); free(status); return 0; }

    int picked = 0;
    for (long i = 0; i < hot_sz && picked < maxwant; i++) {
        int on_dst = (status[i] == dst_node);
        int on_src = (status[i] == src_node);
        int ok = only_src ? on_src : (!on_dst && status[i] >= 0);
        if (ok) {
            batch_pages[picked] = addrs[i];
            batch_nodes[picked] = dst_node;
            picked++;
        }
    }
    free(addrs); free(status);
    return picked;
}

static void *migrate_thread(void *arg_) {
    long midx = (long)(intptr_t)arg_;
    // Pin each migration thread to a different CPU on the dst node
    pin_to_node_roundrobin(CFG.dst_node, (int)midx);

    void **pages = (void**)malloc(sizeof(void*) * CFG.migrate_batch);
    int *nodes = (int*)malloc(sizeof(int) * CFG.migrate_batch);
    int *status = (int*)malloc(sizeof(int) * CFG.migrate_batch);
    if (!pages || !nodes || !status) {
        fprintf(stderr, "alloc batch arrays failed\n");
        return NULL;
    }

    const int flags = CFG.use_move_all ? MPOL_MF_MOVE_ALL : MPOL_MF_MOVE;

    while (!STOP) {
        if (CFG.drain_per_window > 0) {
            // Record the current window base, stop draining this window once it rotates (to avoid infinite draining)
            long window_base = atomic_load_explicit(&HOT_BASE, memory_order_relaxed);
            int rounds = 0;
            while (!STOP && rounds < CFG.drain_per_window) {
                if (atomic_load_explicit(&HOT_BASE, memory_order_relaxed) != window_base) break;

                int n = collect_remote_hot(pages, nodes, CFG.migrate_batch,
                                           CFG.dst_node, CFG.src_node, CFG.only_src);
                if (n <= 0) break;
                if (CFG.restat_before_move) {
                    n = restat_filter(pages, nodes, n, CFG.dst_node, CFG.src_node, CFG.only_src);
                    if (n <= 0) { rounds++; continue; }
                }

                uint64_t t0 = nsec_now();
                int rc = move_pages(0, n, pages, nodes, status, flags);
                uint64_t t1 = nsec_now(); (void)rc;

                int succ = 0, fail = 0;
                for (int i = 0; i < n; i++) {
                    if (status[i] >= 0 && status[i] == CFG.dst_node) succ++;
                    else fail++;
                }
                atomic_fetch_add(&MSTAT.calls, 1);
                atomic_fetch_add(&MSTAT.pages_succ, succ);
                atomic_fetch_add(&MSTAT.pages_fail, fail);
                atomic_fetch_add(&MSTAT.us_sum, (unsigned long)((t1 - t0)/1000));

                if (CFG.migrate_interval_ms > 0)
                    usleep(CFG.migrate_interval_ms * 1000);
                rounds++;
            }
        } else {
            int n = collect_remote_hot(pages, nodes, CFG.migrate_batch,
                                       CFG.dst_node, CFG.src_node, CFG.only_src);
            if (n > 0) {
                if (CFG.restat_before_move) {
                    n = restat_filter(pages, nodes, n, CFG.dst_node, CFG.src_node, CFG.only_src);
                }
                if (n > 0) {
                    uint64_t t0 = nsec_now();
                    int rc = move_pages(0, n, pages, nodes, status, flags);
                    uint64_t t1 = nsec_now(); (void)rc;

                    int succ = 0, fail = 0;
                    for (int i = 0; i < n; i++) {
                        if (status[i] >= 0 && status[i] == CFG.dst_node) succ++;
                        else fail++;
                    }
                    atomic_fetch_add(&MSTAT.calls, 1);
                    atomic_fetch_add(&MSTAT.pages_succ, succ);
                    atomic_fetch_add(&MSTAT.pages_fail, fail);
                    atomic_fetch_add(&MSTAT.us_sum, (unsigned long)((t1 - t0)/1000));
                }
            }
            if (CFG.migrate_interval_ms > 0)
                usleep(CFG.migrate_interval_ms * 1000);
        }
    }

    free(pages); free(nodes); free(status);
    return NULL;
}

// ---------------------- QPS Sampler Thread ----------------------
static void *qps_sampler_thread(void *arg){
    (void)arg;
    if (CFG.qps_sample_ms <= 0) return NULL;
    int ms = CFG.qps_sample_ms;

    QPS_CAP = (CFG.duration_sec * 1000 / ms) + 16;
    QPS_SAMPLES = (double*)malloc(sizeof(double)*QPS_CAP);
    if (!QPS_SAMPLES) return NULL;

    unsigned long last = atomic_load(&WSTAT.ops);
    uint64_t t0 = nsec_now();

    while (!STOP) {
        usleep(ms * 1000);
        unsigned long cur = atomic_load(&WSTAT.ops);
        unsigned long delta = cur - last;
        last = cur;
        double qps = delta / (ms/1000.0);

        pthread_mutex_lock(&QPS_LOCK);
        if (QPS_N < QPS_CAP) QPS_SAMPLES[QPS_N++] = qps;
        pthread_mutex_unlock(&QPS_LOCK);

        if ((nsec_now() - t0)/1000000000ull >= (uint64_t)CFG.duration_sec) break;
    }
    return NULL;
}

// ---------------------- Probe Thread (micro-batch "query" latency) ----------------------
static void *probe_thread(void *arg){
    (void)arg;
    if (CFG.probe_ops <= 0 || CFG.probe_period_ms <= 0) return NULL;

    pin_to_node_roundrobin(CFG.dst_node, 0);

    PROBE_CAP = (CFG.duration_sec * 1000 / CFG.probe_period_ms) + 16;
    PROBE_LAT = (double*)malloc(sizeof(double)*PROBE_CAP);
    if (!PROBE_LAT) return NULL;

    uint64_t seed = 0x1234ULL ^ (uint64_t)pthread_self();

    while (!STOP) {
        usleep(CFG.probe_period_ms * 1000);

        long hb = atomic_load_explicit(&HOT_BASE, memory_order_relaxed);
        uint64_t t0 = nsec_now();
        for (int k = 0; k < CFG.probe_ops; k++) {
            long idx = pick_hot_index(&seed, CFG.pages, CFG.hot_frac, CFG.hot_prob, hb);
            volatile uint64_t *p = (volatile uint64_t*)g_page_ptrs[idx];
            uint64_t v = *p; *p = v + 1;
            // Note: Probing does not increment WSTAT.ops to avoid affecting QPS samples
        }
        uint64_t t1 = nsec_now();
        double us = (t1 - t0)/1000.0;

        pthread_mutex_lock(&PROBE_LOCK);
        if (PROBE_N < PROBE_CAP) PROBE_LAT[PROBE_N++] = us;
        pthread_mutex_unlock(&PROBE_LOCK);
    }
    return NULL;
}

// ---------------------- Argument Parsing ----------------------
static void usage(const char *prog) {
    fprintf(stderr,
    "Usage: sudo %s [options]\n"
    "  --pages N              number of 4KiB pages (default %ld)\n"
    "  --duration SEC         run seconds (default %d)\n"
    "  --workers N            worker threads on dst node (default %d)\n"
    "  --migrates N           migrate threads on dst node (default %d)\n"
    "  --src N                source node for initial placement (default %d)\n"
    "  --dst N                destination node for workers & migration (default %d)\n"
    "  --batch N              migrate batch size per call (default %d)\n"
    "  --migrate-interval MS  throttle between migrate calls (default %d)\n"
    "  --hot-frac F           fraction of pages as hot window (default %.2f)\n"
    "  --hot-prob P           worker hit-probability for hot window (default %.2f)\n"
    "  --hot-rotate SEC       rotate hot window every SEC (default %d=off)\n"
    "  --rotate-step full|quarter  step size per rotate (default quarter)\n"
    "  --drain-per-window N   drain the current window up to N rounds (default 0=off)\n"
    "  --only-src             only migrate pages currently on SRC node\n"
    "  --restat               re-stat the picked batch just before move_pages()\n"
    "  --qps-sample-ms MS     sample QPS every MS ms and print p50/p90/p95/p99 (default 10, 0=off)\n"
    "  --probe OPS PERIOD_MS  enable probe: each 'query' does OPS ops every PERIOD_MS ms\n"
    "  --move-all             use MPOL_MF_MOVE_ALL (needs CAP_SYS_NICE)\n"
    "  --no-verify            disable residency print at start/end\n",
    prog, CFG.pages, CFG.duration_sec, CFG.workers, CFG.migrates, CFG.src_node, CFG.dst_node,
    CFG.migrate_batch, CFG.migrate_interval_ms, CFG.hot_frac, CFG.hot_prob, CFG.hot_rotate_sec);
}

static int parse_args(int argc, char **argv) {
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--pages") && i+1<argc) CFG.pages = atol(argv[++i]);
        else if (!strcmp(argv[i], "--duration") && i+1<argc) CFG.duration_sec = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--workers") && i+1<argc) CFG.workers = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--migrates") && i+1<argc) CFG.migrates = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--src") && i+1<argc) CFG.src_node = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--dst") && i+1<argc) CFG.dst_node = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--batch") && i+1<argc) CFG.migrate_batch = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--migrate-interval") && i+1<argc) CFG.migrate_interval_ms = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--hot-frac") && i+1<argc) CFG.hot_frac = atof(argv[++i]);
        else if (!strcmp(argv[i], "--hot-prob") && i+1<argc) CFG.hot_prob = atof(argv[++i]);
        else if (!strcmp(argv[i], "--hot-rotate") && i+1<argc) CFG.hot_rotate_sec = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--rotate-step") && i+1<argc) {
            const char *v = argv[++i];
            if (!strcmp(v, "full")) CFG.rotate_step_full = 1;
            else if (!strcmp(v, "quarter")) CFG.rotate_step_full = 0;
            else { fprintf(stderr, "invalid --rotate-step\n"); return -1; }
        }
        else if (!strcmp(argv[i], "--drain-per-window") && i+1<argc) CFG.drain_per_window = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--only-src")) CFG.only_src = 1;
        else if (!strcmp(argv[i], "--restat")) CFG.restat_before_move = 1;
        else if (!strcmp(argv[i], "--qps-sample-ms") && i+1<argc) CFG.qps_sample_ms = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--probe") && i+2<argc) { CFG.probe_ops = atoi(argv[++i]); CFG.probe_period_ms = atoi(argv[++i]); }
        else if (!strcmp(argv[i], "--move-all")) CFG.use_move_all = 1;
        else if (!strcmp(argv[i], "--no-verify")) CFG.verify_residency = 0;
        else { usage(argv[0]); return -1; }
    }
    if (CFG.pages <= 0) CFG.pages = 1;
    if (CFG.hot_frac <= 0.0) CFG.hot_frac = 0.01;
    if (CFG.hot_frac > 1.0) CFG.hot_frac = 1.0;
    if (CFG.hot_prob < 0.0) CFG.hot_prob = 0.0;
    if (CFG.hot_prob > 1.0) CFG.hot_prob = 1.0;
    if (CFG.migrate_batch < 1) CFG.migrate_batch = 1;
    if (CFG.drain_per_window < 0) CFG.drain_per_window = 0;
    return 0;
}

// ---------------------- Main Flow ----------------------
int main(int argc, char **argv) {
    if (parse_args(argc, argv) < 0) return 1;

    if (numa_available() < 0) {
        fprintf(stderr, "libnuma says NUMA unavailable\n");
        return 1;
    }
    PAGE_SZ = (size_t)sysconf(_SC_PAGESIZE);

    // Allocate mapping & build page pointers
    size_t bytes = (size_t)CFG.pages * PAGE_SZ;
    g_base = mmap(NULL, bytes, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    if (g_base == MAP_FAILED) { perror("mmap"); return 1; }
    g_page_ptrs = (void**)malloc(sizeof(void*) * CFG.pages);
    if (!g_page_ptrs) { fprintf(stderr, "alloc g_page_ptrs failed\n"); return 1; }
    for (long i = 0; i < CFG.pages; i++)
        g_page_ptrs[i] = (void*)((char*)g_base + (size_t)i * PAGE_SZ);

    fprintf(stderr,
        "Mapping %ld pages (%.3f MiB), src=%d dst=%d, workers=%d, migrates=%d, batch=%d, hot=%.0f%% p=%.0f%% rotate=%ds, step=%s, drain=%d, only-src=%d, restat=%d\n",
        CFG.pages, (double)bytes/(1024.0*1024.0), CFG.src_node, CFG.dst_node,
        CFG.workers, CFG.migrates, CFG.migrate_batch, CFG.hot_frac*100.0, CFG.hot_prob*100.0,
        CFG.hot_rotate_sec, (CFG.rotate_step_full?"full":"quarter"),
        CFG.drain_per_window, CFG.only_src, CFG.restat_before_move);

    // 1) Initial placement on src (first touch)
    initial_place_on_src();
    if (CFG.verify_residency) print_residency_all("start");

    // 2) Start workers (all pinned to dst node CPUs)
    pthread_t *wth = (pthread_t*)malloc(sizeof(pthread_t)*CFG.workers);
    for (int t = 0; t < CFG.workers; t++)
        pthread_create(&wth[t], NULL, worker_thread, (void*)(intptr_t)t);

    // 3) Start migration threads (only migrate remote hot pages to dst)
    pthread_t *mth = (pthread_t*)malloc(sizeof(pthread_t)*CFG.migrates);
    for (int t = 0; t < CFG.migrates; t++)
        pthread_create(&mth[t], NULL, migrate_thread, (void*)(intptr_t)t);

    // 4) Optional hotspot rotation
    pthread_t rth = 0;
    if (CFG.hot_rotate_sec > 0)
        pthread_create(&rth, NULL, hot_rotator_thread, NULL);

    // 5) Observer threads
    pthread_t qth = 0, pth = 0;
    if (CFG.qps_sample_ms > 0)
        pthread_create(&qth, NULL, qps_sampler_thread, NULL);
    if (CFG.probe_ops > 0 && CFG.probe_period_ms > 0)
        pthread_create(&pth, NULL, probe_thread, NULL);

    // 6) Run until duration ends
    uint64_t t0 = nsec_now();
    while (1) {
        sleep(1);
        uint64_t dt = (nsec_now() - t0) / 1000000000ull;
        if ((int)dt >= CFG.duration_sec) break;
    }
    STOP = 1;

    // 7) Cleanup
    for (int t = 0; t < CFG.workers; t++) pthread_join(wth[t], NULL);
    for (int t = 0; t < CFG.migrates; t++) pthread_join(mth[t], NULL);
    if (CFG.hot_rotate_sec > 0) pthread_join(rth, NULL);
    if (CFG.qps_sample_ms > 0) pthread_join(qth, NULL);
    if (CFG.probe_ops > 0 && CFG.probe_period_ms > 0) pthread_join(pth, NULL);

    if (CFG.verify_residency) print_residency_all("end");

    // 8) Summarize
    double sec = (double)CFG.duration_sec;
    unsigned long ops = atomic_load(&WSTAT.ops);
    unsigned long calls = atomic_load(&MSTAT.calls);
    unsigned long p_succ = atomic_load(&MSTAT.pages_succ);
    unsigned long p_fail = atomic_load(&MSTAT.pages_fail);
    unsigned long us_sum = atomic_load(&MSTAT.us_sum);

    double qps = ops / sec;
    double mig_pps = p_succ / sec;
    double avg_ms = calls ? (double)us_sum / 1000.0 / (double)calls : 0.0;
    double per_page_us = (p_succ>0) ? ((double)us_sum / (double)p_succ) : 0.0;

    printf("=== Results ===\n");
    printf("Total ops: %lu\n", ops);
    printf("Query throughput: %.2f ops/s\n", qps);
    printf("Migration calls: %lu\n", calls);
    printf("Avg migration latency: %.3f ms\n", avg_ms);
    printf("Per-successful-page latency: %.3f us/page\n", per_page_us);
    printf("Pages migrated (succ/fail): %lu / %lu\n", p_succ, p_fail);
    printf("Page migration throughput: %.2f pages/s\n", mig_pps);

    // QPS Quantiles
    if (QPS_N > 0) {
        pthread_mutex_lock(&QPS_LOCK);
        qsort(QPS_SAMPLES, QPS_N, sizeof(double), dblcmp);
        double q_min = QPS_SAMPLES[0], q_max = QPS_SAMPLES[QPS_N-1];
        double q_p50 = pct_val(QPS_SAMPLES, QPS_N, 0.50);
        double q_p90 = pct_val(QPS_SAMPLES, QPS_N, 0.90);
        double q_p95 = pct_val(QPS_SAMPLES, QPS_N, 0.95);
        double q_p99 = pct_val(QPS_SAMPLES, QPS_N, 0.99);
        pthread_mutex_unlock(&QPS_LOCK);
        printf("QPS window (%d ms): min=%.2f p50=%.2f p90=%.2f p95=%.2f p99=%.2f max=%.2f ops/s (n=%d)\n",
               CFG.qps_sample_ms, q_min, q_p50, q_p90, q_p95, q_p99, q_max, QPS_N);
    }

    // Probe Quantiles
    if (PROBE_N > 0) {
        pthread_mutex_lock(&PROBE_LOCK);
        qsort(PROBE_LAT, PROBE_N, sizeof(double), dblcmp);
        double l_min = PROBE_LAT[0], l_max = PROBE_LAT[PROBE_N-1];
        double l_p50 = pct_val(PROBE_LAT, PROBE_N, 0.50);
        double l_p90 = pct_val(PROBE_LAT, PROBE_N, 0.90);
        double l_p95 = pct_val(PROBE_LAT, PROBE_N, 0.95);
        double l_p99 = pct_val(PROBE_LAT, PROBE_N, 0.99);
        pthread_mutex_unlock(&PROBE_LOCK);
        printf("Probe latency (N=%d ops): min=%.2f p50=%.2f p90=%.2f p95=%.2f p99=%.2f max=%.2f us (n=%d)\n",
               CFG.probe_ops, l_min, l_p50, l_p90, l_p95, l_p99, l_max, PROBE_N);
    }

    // Resource cleanup
    munmap(g_base, bytes);
    free(g_page_ptrs);
    free(wth);
    free(mth);
    free(QPS_SAMPLES);
    free(PROBE_LAT);
    return 0;
}