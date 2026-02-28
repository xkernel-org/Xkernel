#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/slab.h>
#include <linux/rcupdate.h>
#include <linux/delay.h>
#include <linux/sched.h>
#include <linux/timekeeping.h>
#include <linux/sort.h> // for sort()
#include <linux/spinlock.h>

#define OBJ_SIZE 1024         // Size of each object (1KB)
#define OBJ_COUNT 50000       // Total number of objects to allocate
#define BATCH_SIZE 500
#define BATCH_INTERVAL_MS 1

MODULE_LICENSE("GPL");
MODULE_AUTHOR("YourName");
MODULE_DESCRIPTION("Test kfree_rcu memory reclaim speed (KFREE_DRAIN_JIFFIES sensitive)");

struct test_obj {
    struct rcu_head rcu;
    ktime_t alloc_time; // record allocation time
    char data[OBJ_SIZE - sizeof(struct rcu_head) - sizeof(ktime_t)];
};

static ktime_t start_time;
static ktime_t end_time;
static atomic_t free_count = ATOMIC_INIT(0);

#define DELAY_ARR_SIZE OBJ_COUNT
static u64 *delay_arr;
static atomic_t delay_idx = ATOMIC_INIT(0);

static ktime_t last_batch_time;
static atomic_t batch_counter = ATOMIC_INIT(0);
static spinlock_t batch_lock;

static int cmp_u64(const void *a, const void *b)
{
    u64 va = *(const u64 *)a;
    u64 vb = *(const u64 *)b;
    if (va < vb) return -1;
    if (va > vb) return 1;
    return 0;
}

static void print_delay_stats(void)
{
    int n = atomic_read(&delay_idx);
    if (!delay_arr || n == 0) {
        pr_info("No delay data to report\n");
        return;
    }
    sort(delay_arr, n, sizeof(u64), cmp_u64, NULL);
    #define PERCENTILE(p) delay_arr[(n * (p) / 100)]
    pr_info("Delay(us) stats: p50=%llu, p90=%llu, p99=%llu, max=%llu\n",
        PERCENTILE(50), PERCENTILE(90), PERCENTILE(99), delay_arr[n-1]);
}

static void test_rcu_free(struct rcu_head *rcu)
{
    struct test_obj *obj = container_of(rcu, struct test_obj, rcu);
    ktime_t free_time = ktime_get();
    u64 delay = ktime_to_ns(ktime_sub(free_time, obj->alloc_time)) / 1000; // us
    int idx = atomic_inc_return(&delay_idx) - 1;

    if (delay_arr && idx < DELAY_ARR_SIZE) {
        delay_arr[idx] = delay;
    }

    // 批次间隔统计
    if ((atomic_read(&free_count) % BATCH_SIZE) == 0) {
        ktime_t now = ktime_get();
        long long interval = 0;
        unsigned long flags;
        spin_lock_irqsave(&batch_lock, flags);
        if (last_batch_time) {
            interval = ktime_to_us(ktime_sub(now, last_batch_time));
            pr_info("Batch %d interval: %lld us\n", atomic_inc_return(&batch_counter), interval);
        }
        last_batch_time = now;
        spin_unlock_irqrestore(&batch_lock, flags);
    }

    if (atomic_inc_return(&free_count) == OBJ_COUNT) {
        end_time = ktime_get();
        pr_info("All objects freed! Time elapsed: %lld ms\n",
                ktime_to_ms(ktime_sub(end_time, start_time)));
        print_delay_stats();
    }
}

static int __init test_kfree_rcu_init(void)
{
    int i, j;
    struct test_obj *obj;

    delay_arr = kmalloc_array(DELAY_ARR_SIZE, sizeof(u64), GFP_KERNEL);
    if (!delay_arr) {
        pr_err("Failed to allocate delay_arr\n");
        return -ENOMEM;
    }
    atomic_set(&delay_idx, 0);
    pr_info("Starting kfree_rcu test: allocating %d objects\n", OBJ_COUNT);
    start_time = ktime_get();

    spin_lock_init(&batch_lock);
    last_batch_time = 0;
    atomic_set(&batch_counter, 0);

    // Pin CPU to 5
    cpumask_t cpumask;
    cpumask_clear(&cpumask);
    cpumask_set_cpu(5, &cpumask);
    set_cpus_allowed_ptr(current, &cpumask);
    pr_info("CPU %d pinned\n", smp_processor_id());

    for (i = 0; i < OBJ_COUNT; i += BATCH_SIZE) {
        for (j = 0; j < BATCH_SIZE && i + j < OBJ_COUNT; ++j) {
            obj = kmalloc(sizeof(*obj), GFP_KERNEL);
            if (!obj) {
                pr_err("Allocation failed at %d\n", i + j);
                kfree(delay_arr);
                return -ENOMEM;
            }
            obj->alloc_time = ktime_get();
            memset(obj->data, 0xA5, sizeof(obj->data));
            call_rcu(&obj->rcu, test_rcu_free);
        }
        msleep(BATCH_INTERVAL_MS);
    }

    pr_info("All objects scheduled for call_rcu\n");
    return 0;
}

static void __exit test_kfree_rcu_exit(void)
{
    kfree(delay_arr);
    pr_info("test_kfree_rcu module exit\n");
}

module_init(test_kfree_rcu_init);
module_exit(test_kfree_rcu_exit);