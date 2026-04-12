// SPDX-License-Identifier: GPL-2.0
/*
 * core.c — Xkernel global consistency module (Mode 2)
 *
 * Implements the stop_machine-based global transition protocol:
 *   1. module_init:  stop_machine + stack scan → identify threads in SS
 *   2. daemon thread: poll refcount until all threads exit SS
 *   3. module_exit:   reverse transition (same protocol)
 *
 * The refcount is incremented by stop_machine for each thread found inside
 * SS, and decremented at runtime by auxiliary kprobes at SS exit points.
 */

#define pr_fmt(fmt) "xkernel: " fmt

#include "core.h"
#include "kprobe.h"

#include <linux/fs.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/kthread.h>
#include <linux/ktime.h>
#include <linux/module.h>
#include <linux/sched.h>
#include <linux/sched/signal.h>
#include <linux/stacktrace.h>
#include <linux/stop_machine.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Zhongjie Chen");
MODULE_DESCRIPTION("Xkernel global consistency transition (Mode 2)");

/* ── File paths (populated by userspace loader) ──────────────────── */

#define CS_FILE			"/dev/shm/xkernel/cs"
#define SS_FILE			"/dev/shm/xkernel/ss"
#define TIMING_FILE		"/dev/shm/xkernel/transition_timing"

/* ── Module parameters ───────────────────────────────────────────── */

static int timeout_sec = 5;
module_param(timeout_sec, int, 0644);
MODULE_PARM_DESC(timeout_sec, "Timeout in seconds for transition (default: 5)");

static int poll_interval_ms = 1;
module_param(poll_interval_ms, int, 0644);
MODULE_PARM_DESC(poll_interval_ms,
		 "Daemon polling interval in ms for refcount check (default: 1)");

/* ── Globals ─────────────────────────────────────────────────────── */

LIST_HEAD(xk_target_funcs);

static struct task_struct	*daemon_task;
static atomic_t			refcount = ATOMIC_INIT(0);
static enum xk_state		state    = XK_STATE_PENDING;
static ktime_t			t_start, t_end;

/* ── State accessors ─────────────────────────────────────────────── */

static inline void set_state(enum xk_state s)  { WRITE_ONCE(state, s); }
static inline enum xk_state get_state(void)    { return READ_ONCE(state); }

/* ── Refcount operations ─────────────────────────────────────────── */

void xk_refcount_reset(void)		{ atomic_set(&refcount, 0); }
int  xk_refcount_read(void)		{ return atomic_read(&refcount); }
void xk_refcount_inc(void)		{ atomic_inc(&refcount); }
int  xk_refcount_inc_not_zero(void)	{ return atomic_inc_not_zero(&refcount); }
void xk_refcount_dec(void)		{ atomic_dec(&refcount); }
int  xk_refcount_dec_if_positive(void)	{ return atomic_dec_if_positive(&refcount); }

/* ── Transition timing ───────────────────────────────────────────── */

void xk_record_end_time(void)
{
	cmpxchg64((s64 *)&t_end, 0, ktime_get());
}

/**
 * write_transition_timing() - Write timing data to TIMING_FILE.
 *
 * Writes a simple key=value text file so userspace can read transition
 * latency without parsing dmesg.  Called from the daemon after each
 * completed (or failed) transition.
 *
 * Format:
 *   start_ns=<nanoseconds>
 *   end_ns=<nanoseconds>
 *   elapsed_us=<microseconds>
 *   direction=forward|reverse
 */
static void write_transition_timing(s64 start_ns, s64 end_ns,
				    s64 elapsed_us, bool is_reverse)
{
	struct file *filp;
	char buf[256];
	int len;
	loff_t pos = 0;

	filp = filp_open(TIMING_FILE, O_WRONLY | O_CREAT | O_TRUNC, 0644);
	if (IS_ERR(filp)) {
		pr_warn("failed to open %s: %ld\n", TIMING_FILE, PTR_ERR(filp));
		return;
	}

	len = scnprintf(buf, sizeof(buf),
			"start_ns=%lld\nend_ns=%lld\nelapsed_us=%lld\ndirection=%s\n",
			start_ns, end_ns, elapsed_us,
			is_reverse ? "reverse" : "forward");

	kernel_write(filp, buf, len, &pos);
	filp_close(filp, NULL);
}

/* ── Stack inspection (runs inside stop_machine) ─────────────────── */

static unsigned long stack_buf[XK_MAX_STACK_ENTRIES];

#ifdef DEBUG
static void print_stack(struct task_struct *task, unsigned long *entries, int n)
{
	int i;

	pr_info("stack trace for [%s/%d]:\n", task->comm, task->pid);
	for (i = 0; i < n; i++)
		pr_info("  [%d] %pS\n", i, (void *)entries[i]);
}
#else
static inline void print_stack(struct task_struct *t, unsigned long *e, int n) {}
#endif

/**
 * check_task_in_spans() - Check whether any stack frame is inside a span.
 *
 * Increments the global refcount **once per matching (frame, span) pair**.
 * This is intentional: for a recursively-called function that appears N times
 * on the stack, refcount is incremented N times.  Each return through the SS
 * exit point fires the unguard kprobe exactly once, so refcount is decremented
 * N times symmetrically.
 *
 * NOTE: Spans in xk_target_funcs must not overlap.  If two distinct
 * xk_target_func entries cover the same address, a single frame would be
 * counted twice, breaking the refcount symmetry.  The loader ensures
 * non-overlapping spans.
 *
 * If a match is found, increment the global refcount so the daemon knows
 * to wait for that thread to exit SS.
 */
static bool check_task_in_spans(struct task_struct *task,
				unsigned long *entries, int n)
{
	struct xk_target_func *func;
	bool found = false;
	int i;

	list_for_each_entry(func, &xk_target_funcs, list) {
		for (i = 0; i < n; i++) {
			if (!xk_addr_in_span(entries[i], func->addr,
					     func->soff, func->eoff))
				continue;

			pr_info("%s [0x%lx,0x%lx] found in [%s/%d] stack\n",
				func->name, func->soff, func->eoff,
				task->comm, task->pid);
			xk_refcount_inc();
			found = true;
		}
	}

	if (found)
		print_stack(task, entries, n);

	return found;
}

static int save_stack(struct task_struct *task)
{
	int n;

	n = stack_trace_save_tsk(task, stack_buf, XK_MAX_STACK_ENTRIES, 0);
	if (n == 0 && strncmp(task->comm, "migration/", 10) != 0) {
		pr_err("failed to save stack for [%s/%d]\n",
		       task->comm, task->pid);
		return -1;
	}
	return n;
}

/**
 * stop_machine_check_stacks() - Scan all threads for SS occupancy.
 *
 * Called via stop_machine().  If any thread is inside SS, the refcount
 * is set and auxiliary kprobes are enabled so they can decrement it.
 */
static int stop_machine_check_stacks(void *data)
{
	struct task_struct *g, *task;
	bool need_wait = false;
	int n;

	for_each_process_thread(g, task) {
		n = save_stack(task);
		if (n < 0)
			return 0;
		if (n == 0)
			continue;
		need_wait |= check_task_in_spans(task, stack_buf, n);
	}

	if (need_wait) {
		pr_info("initial refcount: %d\n", xk_refcount_read());
		xk_enable_aux_kprobes();
		t_start = ktime_get();
	}
	/* If !need_wait: no threads in SS → transition is instant.
	 * Userspace sets xk_active=1 via BSS update after module completes. */

	return 0;
}

/* ── File I/O — read span ranges ─────────────────────────────────── */

static int read_spans_from_file(const char *path)
{
	struct file *filp;
	loff_t pos = 0;
	char buf[256];
	ssize_t bytes;
	int ret = 0;

	filp = filp_open(path, O_RDONLY, 0);
	if (IS_ERR(filp))
		return -ENOENT;

	while ((bytes = kernel_read(filp, buf, sizeof(buf) - 1, &pos)) > 0) {
		char *line, *cur;

		buf[bytes] = '\0';
		cur = buf;

		while ((line = strsep(&cur, "\n")) != NULL) {
			struct xk_target_func *func;
			char *p, *tok, *tokens[4];
			int i = 0;

			if (*line == '\0')
				continue;

			p = line;
			while ((tok = strsep(&p, ",")) && i < 4)
				tokens[i++] = tok;
			if (i != 4) {
				pr_err("malformed line in %s: %s\n", path, line);
				continue;
			}

			func = kmalloc(sizeof(*func), GFP_KERNEL);
			if (!func) {
				ret = -ENOMEM;
				goto out;
			}

			strscpy(func->name, tokens[0], XK_MAX_FUNC_NAME_LEN);
			if (kstrtoul(tokens[1], 0, &func->addr) ||
			    kstrtoul(tokens[2], 0, &func->soff) ||
			    kstrtoul(tokens[3], 0, &func->eoff)) {
				pr_err("failed to parse: %s\n", line);
				kfree(func);
				continue;
			}

			if (func->soff == func->eoff) {
				pr_info("skip zero-width span: %s\n",
					func->name);
				kfree(func);
				continue;
			}

			INIT_LIST_HEAD(&func->list);
			list_add_tail(&func->list, &xk_target_funcs);

			pr_info("span: %s @ 0x%lx [0x%lx, 0x%lx]\n",
				func->name, func->addr, func->soff, func->eoff);
		}
	}

	if (bytes < 0) {
		pr_err("read error on %s: %zd\n", path, bytes);
		ret = -EIO;
	}
out:
	filp_close(filp, NULL);
	return ret;
}

/**
 * load_target_spans() - Load SS (or CS as fallback) span ranges.
 *
 * Tries Safe Span file first.  If not available, falls back to
 * Critical Span file as a conservative approximation.
 */
static int load_target_spans(void)
{
	int ret;

	ret = read_spans_from_file(SS_FILE);
	if (ret == 0) {
		pr_info("loaded safe spans from %s\n", SS_FILE);
		return 0;
	}

	pr_info("SS not available, falling back to CS\n");
	ret = read_spans_from_file(CS_FILE);
	if (ret)
		pr_err("failed to read spans from %s\n", CS_FILE);

	return ret;
}

static void free_target_spans(void)
{
	struct xk_target_func *func, *tmp;

	list_for_each_entry_safe(func, tmp, &xk_target_funcs, list) {
		list_del(&func->list);
		kfree(func);
	}
}

/* ── Daemon thread ───────────────────────────────────────────────── */

static int transition_daemon(void *data)
{
	int poll_count = 0;
	int max_polls;

	while (!kthread_should_stop()) {
		enum xk_state s = get_state();

		/* Recompute max_polls each wakeup to honour module_param changes */
		max_polls = timeout_sec * 1000 / max(poll_interval_ms, 1);

		/* Terminal states — sleep until kthread_stop() */
		if (s == XK_STATE_DONE || s == XK_STATE_FAILED ||
		    s == XK_STATE_REVERSE_DONE || s == XK_STATE_REVERSE_FAILED) {
			set_current_state(TASK_INTERRUPTIBLE);
			schedule();
			continue;
		}

		/* Waiting for refcount → 0 */
		if (xk_refcount_read() == 0) {
			/*
			 * Ensure t_end (written by a kprobe handler on another
			 * CPU via cmpxchg64) is visible before we read it.
			 * The atomic_read above provides a control dependency on
			 * x86 but not on weakly-ordered architectures.
			 */
			smp_rmb();
			ktime_t te      = READ_ONCE(t_end);
			ktime_t ts      = t_start;
			s64 start_ns    = ktime_to_ns(ts);
			s64 end_ns      = ktime_to_ns(te);
			s64 elapsed     = ktime_to_us(ktime_sub(te, ts));
			bool is_reverse = (s == XK_STATE_REVERSE_PENDING);

			pr_info("%stransition done, time: %lld us\n",
				is_reverse ? "reverse " : "", elapsed);

			write_transition_timing(start_ns, end_ns, elapsed,
						is_reverse);

			WRITE_ONCE(t_start, 0);
			WRITE_ONCE(t_end, 0);

			WARN_ON_ONCE(!xk_aux_kprobes_enabled());
			xk_detach_aux_kprobes();
			set_state(is_reverse ? XK_STATE_REVERSE_DONE
					     : XK_STATE_DONE);

			poll_count = 0;
			set_current_state(TASK_INTERRUPTIBLE);
			schedule();
		} else {
			set_current_state(TASK_INTERRUPTIBLE);
			schedule_timeout(msecs_to_jiffies(max(poll_interval_ms, 1)));

			if (++poll_count > max_polls) {
				bool is_reverse = (s == XK_STATE_REVERSE_PENDING);

				pr_err("%stransition timed out\n",
				       is_reverse ? "reverse " : "");
				write_transition_timing(ktime_to_ns(t_start),
							0, -1, is_reverse);
				WARN_ON_ONCE(!xk_aux_kprobes_enabled());
				xk_detach_aux_kprobes();
				set_state(is_reverse ? XK_STATE_REVERSE_FAILED
						     : XK_STATE_FAILED);
				poll_count = 0;
			}
		}
	}

	return 0;
}

/* ── Module init / exit ──────────────────────────────────────────── */

static int __init consistency_init(void)
{
	int ret;

	pr_info("module loaded (timeout=%ds, poll_interval=%dms)\n",
		timeout_sec, poll_interval_ms);

	INIT_LIST_HEAD(&xk_target_funcs);

	daemon_task = kthread_create(transition_daemon, NULL, "xk-transition");
	if (IS_ERR(daemon_task)) {
		pr_err("failed to create daemon thread\n");
		return PTR_ERR(daemon_task);
	}

	ret = load_target_spans();
	if (ret) {
		pr_err("failed to load target spans\n");
		return ret;
	}

	/*
	 * register_kprobe() cannot be called inside stop_machine, so
	 * attach kprobes now (disabled) and enable inside the callback.
	 */
	ret = xk_attach_aux_kprobes(/*forward=*/true);
	if (ret) {
		pr_err("failed to attach auxiliary kprobes\n");
		return ret;
	}

	set_state(XK_STATE_PENDING);
	stop_machine(stop_machine_check_stacks, NULL, NULL);

	if (xk_aux_kprobes_enabled()) {
		pr_info("waiting for forward transition...\n");
		wake_up_process(daemon_task);
	} else {
		ktime_t now = ktime_get();
		s64 now_ns = ktime_to_ns(now);

		pr_info("transition instant (no threads in SS)\n");
		write_transition_timing(now_ns, now_ns, 0, false);
		xk_detach_aux_kprobes();
		set_state(XK_STATE_DONE);
	}

	return 0;
}

static void __exit consistency_exit(void)
{
	/* Wait for forward transition to finish */
	while (get_state() == XK_STATE_PENDING)
		cpu_relax();

	if (get_state() != XK_STATE_FAILED) {
		int ret = xk_attach_aux_kprobes(/*forward=*/false);

		if (ret) {
			pr_err("failed to attach reverse kprobes\n");
			goto out;
		}

		stop_machine(stop_machine_check_stacks, NULL, NULL);

		if (xk_aux_kprobes_enabled()) {
			set_state(XK_STATE_REVERSE_PENDING);
			pr_info("waiting for reverse transition...\n");
			wake_up_process(daemon_task);
		} else {
			ktime_t now = ktime_get();
			s64 now_ns = ktime_to_ns(now);

			pr_info("reverse transition instant\n");
			write_transition_timing(now_ns, now_ns, 0, true);
			xk_detach_aux_kprobes();
			set_state(XK_STATE_REVERSE_DONE);
		}

		while (get_state() == XK_STATE_REVERSE_PENDING)
			cpu_relax();
	}

out:
	if (daemon_task) {
		kthread_stop(daemon_task);
		daemon_task = NULL;
	}
	free_target_spans();

	pr_info("module unloaded\n");
}

module_init(consistency_init);
module_exit(consistency_exit);
