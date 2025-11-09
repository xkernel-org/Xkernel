// build: make -C /lib/modules/$(uname -r)/build M=$PWD modules
#include <linux/module.h>
#include <linux/workqueue.h>
#include <linux/ktime.h>

static unsigned int loops = 200000;
module_param(loops, uint, 0644);
static unsigned int spin_ns = 20000;  // 每次work忙等时间，原子上下文不可睡眠
module_param(spin_ns, uint, 0644);

static struct workqueue_struct *wq;
static struct work_struct work;
static atomic_t cnt = ATOMIC_INIT(0);

static void bh_workfn(struct work_struct *ws)
{
    ktime_t start = ktime_get();
    while ((u64)ktime_to_ns(ktime_sub(ktime_get(), start)) < spin_ns)
        cpu_relax();                    // 忙等，拉长一次回调耗时

    if (atomic_inc_return(&cnt) < loops)
        queue_work(wq, &work);          // 在 BH 上下文里自我重排队
}

static int __init bh_test_init(void)
{
    wq = alloc_workqueue("bh_test", WQ_BH | WQ_HIGHPRI, 0); // 关键：WQ_BH
    if (!wq) return -ENOMEM;
    INIT_WORK(&work, bh_workfn);
    queue_work(wq, &work);
    pr_info("bh_test: queued %u loops, spin %u ns\n", loops, spin_ns);
    return 0;
}

static void __exit bh_test_exit(void)
{
    if (wq) {
        cancel_work_sync(&work);
        destroy_workqueue(wq);
    }
    pr_info("bh_test: ran %d iterations\n", atomic_read(&cnt));
}
module_init(bh_test_init);
module_exit(bh_test_exit);
MODULE_LICENSE("GPL");
