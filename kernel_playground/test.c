#include <linux/module.h>
#include <linux/init.h>
#include <linux/bpf.h>
#include <linux/btf.h>
#include <linux/btf_ids.h>
#include <linux/kernel.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Zhongjie");
MODULE_DESCRIPTION("A kernel module for test");

#define MAGIC_NUMBER 16

static int __init test_init(void)
{
	pr_info("test module loaded\n");
	return 0;
}

void xkernel_test_func1(void);
void xkernel_test_func2(void);

void xkernel_test_func1(void)
{
	u32 *magic_number;
	magic_number = kmalloc(sizeof(u32), GFP_KERNEL);
	if (!magic_number) {
		pr_err("failed to allocate memory\n");
		return;
	}

	*magic_number = 20;

	if (*magic_number > MAGIC_NUMBER) {
		pr_info("magic_number > MAGIC_NUMBER\n");
		pr_info("magic_number: %d\n", *magic_number);
		kfree(magic_number);
		return;
	}
	pr_info("magic_number <= MAGIC_NUMBER\n");
	pr_info("magic_number: %d\n", *magic_number);

	kfree(magic_number);
}
void xkernel_test_func2(void)
{
	u32 *magic_number;
	magic_number = kmalloc(sizeof(u32), GFP_KERNEL);
	if (!magic_number) {
		pr_err("failed to allocate memory\n");
		return;
	}

	*magic_number = 16;

	if (*magic_number > MAGIC_NUMBER) {
		pr_info("magic_number > MAGIC_NUMBER\n");
		pr_info("magic_number: %d\n", *magic_number);
		kfree(magic_number);
		return;
	}
	pr_info("magic_number <= MAGIC_NUMBER\n");
	pr_info("magic_number: %d\n", *magic_number);
	kfree(magic_number);
}

EXPORT_SYMBOL(xkernel_test_func1);
EXPORT_SYMBOL(xkernel_test_func2);


static void __exit test_exit(void)
{
	pr_info("test module unloaded\n");

	xkernel_test_func1();
}

module_init(test_init);
module_exit(test_exit);

