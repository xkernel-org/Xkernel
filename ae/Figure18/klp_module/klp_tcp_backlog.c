// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * klp_tcp_backlog.c — KLP module patching tcp_sendmsg_locked
 *
 * This module registers a live patch for tcp_sendmsg_locked() to measure
 * KLP transition time. The patched function is a trivial replacement
 * (returns -EOPNOTSUPP) — correctness is irrelevant since we only
 * measure how long it takes for ALL tasks to exit the old function.
 *
 * The key insight: with 128 iperf3 threads stuck in tcp_sendmsg_locked
 * (tiny window -w 4k), KLP must wait for every thread to voluntarily
 * exit before the transition completes. This can take many seconds.
 */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/livepatch.h>
#include <linux/socket.h>
#include <net/sock.h>

static int livepatch_tcp_sendmsg_locked(struct sock *sk,
					struct msghdr *msg, size_t size)
{
	return -EOPNOTSUPP;
}

static struct klp_func funcs[] = {
	{
		.old_name = "tcp_sendmsg_locked",
		.new_func = livepatch_tcp_sendmsg_locked,
	}, { }
};

static struct klp_object objs[] = {
	{
		/* NULL name means vmlinux */
		.funcs = funcs,
	}, { }
};

static struct klp_patch patch = {
	.mod = THIS_MODULE,
	.objs = objs,
};

static int __init klp_tcp_init(void)
{
	pr_info("patching tcp_sendmsg_locked (process_backlog threshold)\n");
	return klp_enable_patch(&patch);
}

static void __exit klp_tcp_exit(void)
{
	pr_info("unloaded\n");
}

module_init(klp_tcp_init);
module_exit(klp_tcp_exit);
MODULE_LICENSE("GPL");
MODULE_INFO(livepatch, "Y");
MODULE_DESCRIPTION("KLP patch for tcp_sendmsg_locked (Figure 18 benchmark)");
