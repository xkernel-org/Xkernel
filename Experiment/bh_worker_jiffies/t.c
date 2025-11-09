// SPDX-License-Identifier: GPL-2.0
#include <linux/module.h>
#include <linux/workqueue.h>
#include <linux/debugfs.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/ktime.h>
#include <linux/cpu.h>

static struct work_struct *works;
static unsigned int nworks = 4096;      // 一次触发排队多少个 work
static unsigned int spin_us = 100;      // 每个 work 忙等多少微秒（BH 不可睡眠）

static void bh_fn(struct work_struct *w)
{
	u64 end = ktime_get_ns() + (u64)spin_us * 1000ULL;
	while (ktime_get_ns() < end)
		cpu_relax();
}

static struct dentry *dir;

static ssize_t cfg_write(struct file *f, const char __user *ubuf, size_t len, loff_t *ppos)
{
	char buf[64];
	unsigned int a, b;
	if (len >= sizeof(buf)) return -EINVAL;
	if (copy_from_user(buf, ubuf, len)) return -EFAULT;
	buf[len] = '\0';
	if (sscanf(buf, "%u %u", &a, &b) == 2) {
		nworks = a ? a : nworks;
		spin_us = b ? b : spin_us;
	}
	return len;
}

static const struct file_operations cfg_fops = {
	.owner = THIS_MODULE,
	.write = cfg_write,
};

static ssize_t kick_write(struct file *f, const char __user *ubuf, size_t len, loff_t *ppos)
{
	unsigned int i;
	for (i = 0; i < nworks; i++)
		queue_work(system_bh_wq, &works[i]); // 直接进 BH WQ
	return len;
}

static const struct file_operations kick_fops = {
	.owner = THIS_MODULE,
	.write = kick_write,
};

static int __init bh_test_init(void)
{
	unsigned int i;
	works = kcalloc(nworks, sizeof(*works), GFP_KERNEL);
	if (!works) return -ENOMEM;
	for (i = 0; i < nworks; i++)
		INIT_WORK(&works[i], bh_fn);

	dir = debugfs_create_dir("bh_wq_test", NULL);
	debugfs_create_file("config", 0600, dir, NULL, &cfg_fops); // "nworks spin_us"
	debugfs_create_file("kick",   0200, dir, NULL, &kick_fops); // 写任意内容触发

	pr_info("bh_wq_test loaded: nworks=%u spin_us=%u\n", nworks, spin_us);
	return 0;
}

static void __exit bh_test_exit(void)
{
	debugfs_remove_recursive(dir);
	// 确保没有在跑的 work
	flush_workqueue(system_bh_wq);
	kfree(works);
}

module_init(bh_test_init);
module_exit(bh_test_exit);
MODULE_LICENSE("GPL");
