#include <linux/module.h>
#include <linux/init.h>
#include <linux/bpf.h>
#include <linux/btf.h>
#include <linux/btf_ids.h>
#include <linux/kernel.h>

#include "test.h"

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Zhongjie");
MODULE_DESCRIPTION("A kernel module for xkernel test");

/**
 * @brief Test condition branch
 */
XKERNEL_TEST_DEFINE(condition_branch)
{
	#define MAGIC_NUMBER 16
	
	u32 *var;
	var = kmalloc(sizeof(u32), GFP_KERNEL);
	if (!var) {
		pr_err("failed to allocate memory\n");
		return;
	}

	*var = 20;

	pr_info("Before check, var: %d, MAGIC_NUMBER: %d\n", *var, MAGIC_NUMBER);

	if (*var > MAGIC_NUMBER) {
		pr_info("var > MAGIC_NUMBER\n");
		pr_info("After check, var: %d\n", *var);
		kfree(var);
		return;
	}
	pr_info("var <= MAGIC_NUMBER\n");
	pr_info("After check, var: %d\n", *var);

	kfree(var);
}

static int __init xkernel_test_init(void)
{
	pr_info("xkernel test module loaded\n");
	return 0;
}

static void __exit xkernel_test_exit(void)
{
	pr_info("xkernel test module unloaded\n");

	XKERNEL_TEST_RUN(condition_branch);
}

module_init(xkernel_test_init);
module_exit(xkernel_test_exit);

