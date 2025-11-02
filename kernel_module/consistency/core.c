#include "core.h"

#include <linux/cpumask.h>
#include <linux/fs.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/kthread.h>
#include <linux/module.h>
#include <linux/sched.h>
#include <linux/sched/signal.h>
#include <linux/stacktrace.h>
#include <linux/stop_machine.h>
#include <linux/uaccess.h>
#include <linux/version.h>
#include <net/sock.h>

#include "kprobe.h"

#define DEBUG

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Zhongjie");
MODULE_DESCRIPTION("A kernel module for Xkernel's consistency model");

#define TARGET_FUNCTIONS_FILE "/dev/shm/xkernel/target_functions"

LIST_HEAD(xk_target_functions);

#define MAX_STACK_ENTRIES 100
static unsigned long xk_stack_entries[MAX_STACK_ENTRIES];

#define INTERVAL_MS 1

static int kTimeout = 5;
module_param(kTimeout, int, 0644);
MODULE_PARM_DESC(kTimeout,
                 "Timeout seconds for the transition. Default: 5s");

static struct task_struct *daemon_task = NULL;

ktime_t start = 0;
ktime_t end = 0;

// Global refcount
atomic_t xk_global_refcount = ATOMIC_INIT(0);
static enum xkernel_state xk_state = XK_FLAGS_PENDING;

#define REF_HASH_BITS 8
static DEFINE_SPINLOCK(ref_hash_lock);
static DEFINE_HASHTABLE(ref_hash_table, REF_HASH_BITS);
static atomic_t ref_hash_size = ATOMIC_INIT(0);

// xk-kfuncs.ko
extern int kMode;
extern bool ir_kprobes_on;
extern int transition;
struct transition_task {
  pid_t pid;
  struct hlist_node node;
  struct rcu_head rcu;
};
#define TRANSITION_TASK_HASH_BITS 8
extern struct hlist_head
    transition_task_hash_table[1 << TRANSITION_TASK_HASH_BITS];

void ref_hash_spinlock(unsigned long flags) {
  spin_lock_irqsave(&ref_hash_lock, flags);
}

void ref_hash_spinunlock(unsigned long flags) {
  spin_unlock_irqrestore(&ref_hash_lock, flags);
}

// This function must be called under the ref_hash_lock lock.
struct xk_refcount *find_or_alloc_refcount(pid_t pid) {
  struct xk_refcount *ref;

  int bucket = hash_32(pid, REF_HASH_BITS);
  struct hlist_node *tmp;
  hlist_for_each_entry_safe(ref, tmp, &ref_hash_table[bucket], node) {
    if (ref->pid == pid) {
      return ref;
    }
  }

  ref = kmalloc(sizeof(*ref), GFP_ATOMIC);
  if (!ref) {
    return NULL;
  }

  ref->pid = pid;
  atomic_set(&ref->refcount, 0);
  ref->start = 0;
  hlist_add_head(&ref->node, &ref_hash_table[bucket]);
  atomic_inc(&ref_hash_size);

  return ref;
}

struct xk_refcount *find_or_fail_refcount(pid_t pid) {
  struct xk_refcount *ref;

  int bucket = hash_32(pid, REF_HASH_BITS);
  struct hlist_node *tmp;
  hlist_for_each_entry_safe(ref, tmp, &ref_hash_table[bucket], node) {
    if (ref->pid == pid) {
      return ref;
    }
  }
  return NULL;
}

void free_refcount(struct xk_refcount *ref) {
  if (ref) {
    hlist_del(&ref->node);
    kfree(ref);
    atomic_dec(&ref_hash_size);
  }
}

// This function must be called under the ref_hash_lock lock.
void find_and_free_refcount(pid_t pid) {
  struct xk_refcount *ref;
  struct hlist_node *tmp;

  int bucket = hash_32(pid, REF_HASH_BITS);

  hlist_for_each_entry_safe(ref, tmp, &ref_hash_table[bucket], node) {
    if (ref->pid == pid) {
      hlist_del(&ref->node);
      kfree(ref);
      break;
    }
  }
}

size_t ref_get_hash_size(void) { return atomic_read(&ref_hash_size); }

static inline void set_xk_state(enum xkernel_state state) {
  WRITE_ONCE(xk_state, state);
}

static inline enum xkernel_state get_xk_state(void) {
  return READ_ONCE(xk_state);
}

// Global
void xk_enable_ir_kprobes(void) { WRITE_ONCE(ir_kprobes_on, true); }
void xk_disable_ir_kprobes(void) { WRITE_ONCE(ir_kprobes_on, false); }
bool xk_is_ir_kprobes_on(void) { return READ_ONCE(ir_kprobes_on); }

// Per-task
void xk_enable_ir_kprobes_task(int v) {
  WARN_ON(v == 0);
  WRITE_ONCE(transition, v);
}

void xk_disable_ir_kprobes_task(void) { WRITE_ONCE(transition, 0); }

#ifdef DEBUG
static void xk_print_stack(struct task_struct *task, unsigned long *entries,
                           int nb_entries) {
  unsigned long address;
  pr_info("Stack trace for task [%s]:\n", task->comm);
  for (int i = 0; i < nb_entries; i++) {
    address = entries[i];
    printk("  [%d] %pS\n", i, (void *)address);
  }
}
#endif

static bool xk_check_functions(struct task_struct *task, unsigned long *entries,
                               int nb_entries) {
  struct xk_target_function *func;
  bool found = false;
  list_for_each_entry(func, &xk_target_functions, list) {
    for (int i = 0; i < nb_entries; i++) {
      if (xk_compare_function(entries[i], func->address, func->soff,
                              func->eoff)) {
        pr_info(
            "Function %s[0x%lx, 0x%lx] found in stack trace for task [%s/%d]\n",
            func->name, func->soff, func->eoff, task->comm, task->pid);
        /**
         * Increment the global/per-task refcount to indicate that the function
         * is being executed. This is used to fix the refcount of the task.
         */

        if (kMode == 1) {
          if (xk_inc_refcount_per_task(task->pid)) {
            pr_err("Failed to increment the refcount for task %s\n",
                   task->comm);
          }

          int bucket = hash_32(task->pid, TRANSITION_TASK_HASH_BITS);
          struct transition_task *ttsk = kmalloc(sizeof(struct transition_task), GFP_ATOMIC);
          if (!ttsk) {
            pr_err("kmalloc failed for transition_task\n");
          } else {
            ttsk->pid = task->pid;
            hlist_add_head_rcu(&ttsk->node,
                               &transition_task_hash_table[bucket]);
          }
        } else {
          xk_inc_refcount();
        }

        found = true;
      }
    }
  }

#ifdef DEBUG
  if (found) {
    xk_print_stack(task, entries, nb_entries);
  }
#endif

  return found;
}

static int xk_dump_stack(struct task_struct *task) {
  int nb_entries;

  nb_entries =
      stack_trace_save_tsk(task, xk_stack_entries, MAX_STACK_ENTRIES, 0);

  if (nb_entries == 0) {
    if (strncmp(task->comm, "migration/", 10) != 0) {
      pr_err("Failed to save stack trace for task %s\n", task->comm);
      return -1;
    }
  }

  return nb_entries;
}

// Note: This function is called in a stop_machine context, so it is not allowed
// to sleep.
static int xk_check_stacks(void *data) {
  bool direction = get_xk_state() == XK_FLAGS_PENDING ? true : false;
  struct task_struct *g, *task;
  unsigned long *entries = xk_stack_entries;
  int nb_entries;
  bool need_transition = false;

  // Traverse all processes and threads to check their stacks.
  for_each_process_thread(g, task) {
    nb_entries = xk_dump_stack(task);
    if (nb_entries < 0)
      return 0;
    if (nb_entries == 0)
      continue;
    need_transition |= xk_check_functions(task, entries, nb_entries);
  }

  if (need_transition) {
    if (kMode == 2) {
      pr_info("Initial refcount: %d\n", xk_refcount());
    }
    xk_enable_auxiliary_kprobes();
    start = ktime_get();
  } else {
    // No target functions are found in the stacks, so we can directly enable or
    // disable the IR kprobes.
    if (direction) {
      if (kMode == 1) {
        xk_enable_ir_kprobes_task(1);
      } else {
        xk_enable_ir_kprobes();
      }
    } else {
      xk_disable_ir_kprobes();
    }
  }

  return 0;
}

static int xk_read_target_functions(void) {
  struct file *filp;
  loff_t pos = 0;
  char buf[256];
  ssize_t bytes;
  int ret = 0;

  filp = filp_open(TARGET_FUNCTIONS_FILE, O_RDONLY, 0);
  if (IS_ERR(filp)) {
    pr_err("Failed to open %s\n", TARGET_FUNCTIONS_FILE);
    return -1;
  }

  // The use of set_fs/get_fs/KERNEL_DS is deprecated and not available in
  // recent kernels. kernel_read() as of 4.14+ does not require set_fs hack; use
  // kernel_read directly.

  while ((bytes = kernel_read(filp, buf, sizeof(buf) - 1, &pos)) > 0) {
    char *line, *cur;
    buf[bytes] = '\0';
    cur = buf;

    while ((line = strsep(&cur, "\n")) != NULL) {
      char *p, *tok;
      char *tokens[4];
      int i = 0;

      if (line[0] == '\0')
        continue;

      p = line;
      while ((tok = strsep(&p, ",")) && i < 4) {
        tokens[i++] = tok;
      }
      if (i != 4) {
        pr_err("Malformed line in %s: %s\n", TARGET_FUNCTIONS_FILE, line);
        continue;
      }

      struct xk_target_function *func = kmalloc(sizeof(*func), GFP_KERNEL);
      if (!func) {
        pr_err("kmalloc failed for xk_target_function\n");
        ret = -ENOMEM;
        goto out;
      }

      strncpy(func->name, tokens[0], MAX_FUNC_NAME_LEN - 1);
      func->name[MAX_FUNC_NAME_LEN - 1] = '\0';
      if (kstrtoul(tokens[1], 0, &func->address)) {
        pr_err("Failed to parse address for function %s\n", tokens[0]);
        kfree(func);
        continue;
      }
      if (kstrtoul(tokens[2], 0, &func->soff)) {
        pr_err("Failed to parse soff for function %s\n", tokens[0]);
        kfree(func);
        continue;
      }
      if (kstrtoul(tokens[3], 0, &func->eoff)) {
        pr_err("Failed to parse eoff for function %s\n", tokens[0]);
        kfree(func);
        continue;
      }

      INIT_LIST_HEAD(&func->list);
      list_add_tail(&func->list, &xk_target_functions);

      pr_info("[Target Functions] [%s] at 0x%lx with span [0x%lx, 0x%lx]\n",
              func->name, func->address, func->soff, func->eoff);
    }
  }
  if (bytes < 0) {
    pr_err("Error reading file %s: %zd\n", TARGET_FUNCTIONS_FILE, bytes);
    ret = -EIO;
  }

out:
  filp_close(filp, NULL);

  if (ret)
    return ret;

  return 0;
}

// Per-task refcount
int xk_refcount_per_task(pid_t pid) {
  struct xk_refcount *ref;
  ref = find_or_alloc_refcount(pid);
  if (!ref) {
    return -ENOENT;
  }
  return atomic_read(&ref->refcount);
}

int xk_inc_refcount_per_task(pid_t pid) {
  struct xk_refcount *ref;
  ref = find_or_alloc_refcount(pid);
  if (!ref) {
    return -ENOMEM;
  }
  ref->start = ktime_get();
  atomic_inc(&ref->refcount);
  return 0;
}

int xk_inc_not_zero_per_task(pid_t pid) {
  struct xk_refcount *ref;
  ref = find_or_fail_refcount(pid);
  if (!ref) {
    return -ENOENT;
  }
  return atomic_inc_not_zero(&ref->refcount);
}

int xk_dec_if_positive_per_task(pid_t pid) {
  struct xk_refcount *ref;
  ref = find_or_fail_refcount(pid);
  if (!ref) {
    return -ENOENT;
  }
  return atomic_dec_if_positive(&ref->refcount);
}

void xk_reset_refcount_per_task(pid_t pid) {
  struct xk_refcount *ref;
  ref = find_or_fail_refcount(pid);
  if (!ref) {
    return;
  }
  atomic_set(&ref->refcount, 0);
}

// Global refcount
int xk_refcount(void) { return atomic_read(&xk_global_refcount); }
void xk_inc_refcount(void) { atomic_inc(&xk_global_refcount); }
int xk_inc_not_zero(void) { return atomic_inc_not_zero(&xk_global_refcount); }
void xk_dec_refcount(void) { atomic_dec(&xk_global_refcount); }
int xk_dec_if_positive(void) {
  return atomic_dec_if_positive(&xk_global_refcount);
}
void xk_reset_refcount(void) { atomic_set(&xk_global_refcount, 0); }

static int daemon_task_main(void *data) {
  int ret = 0;
  int times = 0;
  int times_reverse = 0;

  while (!kthread_should_stop()) {

    if (get_xk_state() == XK_FLAGS_FAILED ||
        get_xk_state() == XK_FLAGS_REVERSE_FAILED ||
        get_xk_state() == XK_FLAGS_DONE ||
        get_xk_state() == XK_FLAGS_REVERSE_DONE) {
      set_current_state(TASK_INTERRUPTIBLE);
      schedule();
      // Let consistency_exit() to stop the daemon task.
      continue;
    }

    if (get_xk_state() == XK_FLAGS_PENDING) {
      if (ref_get_hash_size() == 0) {

        xk_enable_ir_kprobes_task(2);

        // It's time to detach the auxiliary kprobes
        xk_detach_auxiliary_kprobes("daemon_task_main");
        set_xk_state(XK_FLAGS_DONE);
        set_current_state(TASK_INTERRUPTIBLE);
        schedule();
        continue;
      } else {
        set_current_state(TASK_INTERRUPTIBLE);
        schedule_timeout(msecs_to_jiffies(INTERVAL_MS));
        if (times++ > kTimeout * 1000 / INTERVAL_MS) {
          pr_err("[Transition] Transition failed\n");
          xk_detach_auxiliary_kprobes("daemon_task_main");
          set_xk_state(XK_FLAGS_FAILED);
          ret = -ETIMEDOUT;
        }
      }
    } else if (get_xk_state() == XK_FLAGS_REVERSE_PENDING) {
      if (ref_get_hash_size() == 0) {

        xk_enable_ir_kprobes_task(2);

        // It's time to detach the auxiliary kprobes
        xk_detach_auxiliary_kprobes("daemon_task_main");
        set_xk_state(XK_FLAGS_REVERSE_DONE);
        set_current_state(TASK_INTERRUPTIBLE);
        schedule();
        continue;
      }
      set_current_state(TASK_INTERRUPTIBLE);
      schedule_timeout(msecs_to_jiffies(INTERVAL_MS));
      if (times_reverse++ > kTimeout * 1000 / INTERVAL_MS) {
        pr_err("[Reverse Transition] Reverse transition failed\n");
        xk_detach_auxiliary_kprobes("daemon_task_main");
        set_xk_state(XK_FLAGS_REVERSE_FAILED);
        ret = -ETIMEDOUT;
      }
    }
  }

  return ret;
}

static int daemon_main(void *data) {
  int times = 0;
  int times_reverse = 0;
  int ret = 0;

  while (!kthread_should_stop()) {

    if (get_xk_state() == XK_FLAGS_FAILED ||
        get_xk_state() == XK_FLAGS_REVERSE_FAILED ||
        get_xk_state() == XK_FLAGS_DONE ||
        get_xk_state() == XK_FLAGS_REVERSE_DONE) {
      set_current_state(TASK_INTERRUPTIBLE);
      schedule();
      // Let consistency_exit() to stop the daemon task.
      continue;
    }

    if (get_xk_state() == XK_FLAGS_PENDING) {
      if (xk_refcount() == 0) {
        pr_info("[Transition] Transition done, time: %lld us\n",
                ktime_to_us(ktime_sub(end, start)));
        start = end = 0;
        // It's time to detach the auxiliary kprobes
        BUG_ON(!xk_is_auxiliary_kprobes_on());
        xk_detach_auxiliary_kprobes("daemon_main");
        set_xk_state(XK_FLAGS_DONE);

        set_current_state(TASK_INTERRUPTIBLE);
        schedule();
      } else {
        set_current_state(TASK_INTERRUPTIBLE);
        schedule_timeout(msecs_to_jiffies(INTERVAL_MS));
        if (times++ > kTimeout * 1000 / INTERVAL_MS) {
          pr_err("[Transition] Transition failed\n");
          BUG_ON(!xk_is_auxiliary_kprobes_on());
          xk_detach_auxiliary_kprobes("daemon_main");
          set_xk_state(XK_FLAGS_FAILED);
          ret = -ETIMEDOUT;
        }
      }
    } else if (get_xk_state() == XK_FLAGS_REVERSE_PENDING) {
      if (xk_refcount() == 0) {
        // It's time to detach the auxiliary kprobes
        pr_info("[Reverse Transition] Reverse transition done, time: %lld us\n",
                ktime_to_us(ktime_sub(end, start)));
        start = end = 0;
        BUG_ON(!xk_is_auxiliary_kprobes_on());
        xk_detach_auxiliary_kprobes("daemon_main");
        set_xk_state(XK_FLAGS_REVERSE_DONE);

        set_current_state(TASK_INTERRUPTIBLE);
        schedule();
      } else {
        set_current_state(TASK_INTERRUPTIBLE);
        schedule_timeout(msecs_to_jiffies(INTERVAL_MS));
        if (times_reverse++ > kTimeout * 1000 / INTERVAL_MS) {
          pr_err("[Reverse Transition] Reverse transition failed\n");
          BUG_ON(!xk_is_auxiliary_kprobes_on());
          xk_detach_auxiliary_kprobes("daemon_main");
          set_xk_state(XK_FLAGS_REVERSE_FAILED);
          ret = -ETIMEDOUT;
        }
      }
    }
  }
  return ret;
}

static int __init consistency_init(void) {
  pr_info("Xkernel consistency module loaded\n");

  pr_info("Timeout: %d seconds\n", kTimeout);

  if (kMode == 0) {
    pr_info("Immediate consistency model is enabled\n");
    return 0;
  } else if (kMode == 1) {
    pr_info("Per-task consistency model is enabled\n");
  } else {
    pr_info("Global consistency model is enabled\n");
  }

  INIT_LIST_HEAD(&xk_target_functions);

#ifdef DEBUG
  measure_stop_machine_overhead();
#endif
  if (kMode == 1) {
    daemon_task =
        kthread_create(daemon_task_main, NULL, "xkernel-daemon-per-task");
  } else {
    daemon_task = kthread_create(daemon_main, NULL, "xkernel-daemon");
  }
  if (IS_ERR(daemon_task)) {
    pr_err("Failed to create daemon task\n");
    return PTR_ERR(daemon_task);
  }

  if (xk_read_target_functions()) {
    pr_err("Failed to read target functions\n");
    return -1;
  }

  // Since register_kprobe() is not allowed to be called in a stop_machine
  // context, we need to attach the auxiliary kprobes here but don't enable
  // them.
  if (xk_attach_auxiliary_kprobes(true, "consistency_init")) {
    pr_err("Failed to attach auxiliary kprobes\n");
    return -1;
  }

  set_xk_state(XK_FLAGS_PENDING);

  stop_machine(xk_check_stacks, NULL, NULL);

  if (xk_is_auxiliary_kprobes_on()) {
    pr_info("[Transition] Waiting for transition to be done or failed\n");
    wake_up_process(daemon_task);
  } else {
    pr_info("[Transition] Transition done, time: 0 us\n");
    xk_detach_auxiliary_kprobes("consistency_init");
    set_xk_state(XK_FLAGS_DONE);
  }

  return 0;
}

static void __exit consistency_exit(void) {
  pr_info("Xkernel consistency module unloaded\n");

  if (kMode == 0) {
    return;
  }

  while (get_xk_state() == XK_FLAGS_PENDING) {
    // Wait for the transition being done or failed
    cpu_relax();
  }

  if (get_xk_state() == XK_FLAGS_FAILED) {
    goto out;
  }

  // Since register_kprobe() is not allowed to be called in a stop_machine
  // context, we need to attach the auxiliary kprobes here but don't enable
  // them.
  if (xk_attach_auxiliary_kprobes(false, "consistency_exit")) {
    pr_err("Failed to attach auxiliary kprobes\n");
    goto out;
  }

  if (kMode == 1)
    xk_disable_ir_kprobes_task();

  stop_machine(xk_check_stacks, NULL, NULL);

  if (xk_is_auxiliary_kprobes_on()) {
    set_xk_state(XK_FLAGS_REVERSE_PENDING);
    pr_info("[Reverse Transition] Waiting for reverse transition to be done or "
            "failed\n");
    wake_up_process(daemon_task);
  } else {
    BUG_ON(get_xk_state() != XK_FLAGS_DONE);
    pr_info("[Reverse Transition] Reverse transition done, time: 0 us\n");
    xk_detach_auxiliary_kprobes("consistency_exit");
    set_xk_state(XK_FLAGS_REVERSE_DONE);
  }

  while (get_xk_state() == XK_FLAGS_REVERSE_PENDING) {
    // Wait for the reverse transition being done or failed
    cpu_relax();
  }

out:

  if (kMode == 1) {
    struct transition_task *ttsk;
    struct hlist_node *tmp;
    int bucket;
    for (bucket = 0; bucket < 1 << TRANSITION_TASK_HASH_BITS; bucket++) {
      hlist_for_each_entry_safe(ttsk, tmp, &transition_task_hash_table[bucket], node) {
        hlist_del_rcu(&ttsk->node);
        synchronize_rcu();
        kfree(ttsk);
      }
    }
  }

  if (daemon_task) {
    kthread_stop(daemon_task);
    daemon_task = NULL;
  }
}

module_init(consistency_init);
module_exit(consistency_exit);