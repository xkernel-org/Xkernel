#include "core.h"

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/version.h>
#include <linux/stop_machine.h>
#include <linux/sched.h>
#include <linux/sched/signal.h>
#include <linux/cpumask.h>
#include <linux/stacktrace.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/kthread.h>
#include <net/sock.h>

#include "kprobe.h"

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Zhongjie");
MODULE_DESCRIPTION("A kernel module for Xkernel's consistency model");

LIST_HEAD(xk_target_functions);

#define MAX_STACK_ENTRIES 100
static DEFINE_PER_CPU(unsigned long[MAX_STACK_ENTRIES], xk_stack_entries);

#define INTERVAL_MS 1
#define TIMEOUT_TIMES 1000

static struct task_struct *daemon_task = NULL;
static enum xkernel_state xk_state = XK_FLAGS_PENDING;

extern bool ir_kprobes_on;

#define TARGET_FUNCTIONS_FILE "/dev/shm/xkernel/target_functions"

#ifdef DEBUG
static void xk_dump_stack_trace(struct task_struct *task, unsigned long *entries, int nb_entries) {
    unsigned long address;
    pr_info("Stack trace for task [%s]:\n", task->comm);
    for (int i = 0; i < nb_entries; i++) {
        address = entries[i];
        printk("  [%d] %pS\n", i, (void *)address);
    }
}
#endif

void xk_enable_ir_kprobes(void) {
    WRITE_ONCE(ir_kprobes_on, true);
}

void xk_disable_ir_kprobes(void) {
    WRITE_ONCE(ir_kprobes_on, false);
}

static bool xk_check_functions(struct task_struct *task, unsigned long *entries, int nb_entries) {
    struct xk_target_function *func;
    list_for_each_entry(func, &xk_target_functions, list) {
        for (int i = 0; i < nb_entries; i++) {
            if (xk_compare_function(entries[i], func->address, func->size)) {
                pr_info("Function %s found in stack trace for task %s\n", func->name, task->comm);
                /**
                 * Increment the global refcount to indicate that the function is being executed.
                 * This is used to fix the refcount of the task.
                 */
                xk_inc_refcount();

                return true;
            }
        }
    }
    return false;
}

static int xk_dump_stack(struct task_struct *task) {
    unsigned long *entries = this_cpu_ptr(xk_stack_entries);
    int nb_entries;

    nb_entries = stack_trace_save_tsk(task, entries, ARRAY_SIZE(xk_stack_entries), 0);

    if (nb_entries == 0) {
        if (strncmp(task->comm, "migration/", 10) != 0) {
            pr_err("Failed to save stack trace for task %s\n", task->comm);
            return -1;
        }
    }

    return nb_entries;
}

// Note: This function is called in a stop_machine context, so it is not allowed to sleep.
static int xk_check_stacks(void *data) {
    enum xkernel_state state = (enum xkernel_state)data;
    bool direction = state == XK_FLAGS_PENDING ? true : false;
    struct task_struct *g, *task;
    unsigned long *entries = this_cpu_ptr(xk_stack_entries);
    int nb_entries;
    bool need_transition = false;
    
    for_each_process_thread(g, task) {
        nb_entries = xk_dump_stack(task);
        if (nb_entries < 0) return -1;
        if (nb_entries == 0) continue;
        need_transition |= xk_check_functions(task, entries, nb_entries);
    }

    if (need_transition) {
        xk_enable_auxiliary_kprobes();
    } else {
        if (direction) {
            xk_enable_ir_kprobes();
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

    // The use of set_fs/get_fs/KERNEL_DS is deprecated and not available in recent kernels.
    // kernel_read() as of 4.14+ does not require set_fs hack; use kernel_read directly.

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

            strncpy(func->name, tokens[0], MAX_FUNC_NAME_LEN-1);
            func->name[MAX_FUNC_NAME_LEN-1] = '\0';
            if (kstrtoul(tokens[1], 0, &func->address)) {
                pr_err("Failed to parse address for function %s\n", tokens[0]);
                kfree(func);
                continue;
            }
            if (kstrtoul(tokens[2], 0, &func->offset)) {
                pr_err("Failed to parse offset for function %s\n", tokens[0]);
                kfree(func);
                continue;
            }
            if (kstrtoul(tokens[3], 0, &func->size)) {
                pr_err("Failed to parse size for function %s\n", tokens[0]);
                kfree(func);
                continue;
            }            

            INIT_LIST_HEAD(&func->list);
            list_add_tail(&func->list, &xk_target_functions);

            pr_info("[Target Functions] [%s] at 0x%lx with offset 0x%lx and size 0x%lx\n", func->name, func->address, func->offset, func->size);
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

static int daemon_main(void *data) {
    int times = 0;
    int times_reverse = 0;
    int ret = 0;

    while (!kthread_should_stop()) {

        if (READ_ONCE(xk_state) == XK_FLAGS_PENDING) {
            if (xk_refcount() == 0) {
                // It's time to detach the auxiliary kprobes
                BUG_ON(!xk_is_auxiliary_kprobes_on());
                xk_disable_auxiliary_kprobes();
                xk_detach_auxiliary_kprobes();
                pr_info("[Transition] Transition done\n");
                WRITE_ONCE(xk_state, XK_FLAGS_DONE);
                schedule();
            } else {
                schedule_timeout(msecs_to_jiffies(INTERVAL_MS));
                if (times++ > TIMEOUT_TIMES) {
                    BUG_ON(!xk_is_auxiliary_kprobes_on());
                    xk_disable_auxiliary_kprobes();
                    xk_detach_auxiliary_kprobes();
                    pr_err("[Transition] Transition failed\n");
                    WRITE_ONCE(xk_state, XK_FLAGS_FAILED);
                    ret = -ETIMEDOUT;
                    break;
                }
            }
        }
        else if (READ_ONCE(xk_state) == XK_FLAGS_DONE) {
            // Do nothing
            schedule();
        }
        else if (READ_ONCE(xk_state) == XK_FLAGS_REVERSE_PENDING) {
            if (xk_refcount() == 0) {
                // It's time to detach the auxiliary kprobes
                BUG_ON(!xk_is_auxiliary_kprobes_on());
                xk_disable_auxiliary_kprobes();
                xk_detach_auxiliary_kprobes();
                pr_info("[Reverse Transition] Reverse transition done\n");
                WRITE_ONCE(xk_state, XK_FLAGS_REVERSE_DONE);
                schedule();
            } else {
                schedule_timeout(msecs_to_jiffies(INTERVAL_MS));
                if (times_reverse++ > TIMEOUT_TIMES) {
                    BUG_ON(!xk_is_auxiliary_kprobes_on());
                    xk_disable_auxiliary_kprobes();
                    xk_detach_auxiliary_kprobes();
                    pr_err("[Reverse Transition] Reverse transition failed\n");
                    WRITE_ONCE(xk_state, XK_FLAGS_REVERSE_FAILED);
                    ret = -ETIMEDOUT;
                    break;
                }
            }
        }
        else if (READ_ONCE(xk_state) == XK_FLAGS_REVERSE_DONE) {
            break;
        }
    }
    return ret;
}

static int __init consistency_init(void) {
    pr_info("Xkernel consistency module loaded\n");

    INIT_LIST_HEAD(&xk_target_functions);

    measure_stop_machine_overhead();
    
    daemon_task = kthread_create(daemon_main, NULL, "xkernel-daemon");
    if (IS_ERR(daemon_task)) {
        pr_err("Failed to create daemon task\n");
        return PTR_ERR(daemon_task);
    }
    
    if (xk_read_target_functions()) {pr_err("Failed to read target functions\n"); return -1;}

    // Since register_kprobe() is not allowed to be called in a stop_machine context, 
    // we need to attach the auxiliary kprobes here but don't enable them.
    xk_disable_auxiliary_kprobes();
    xk_attach_auxiliary_kprobes(true);

    stop_machine(xk_check_stacks, (void *)xk_state, NULL);

    if (xk_is_auxiliary_kprobes_on()) {
        pr_info("[Transition] Waiting for transition to be done or failed\n");
        wake_up_process(daemon_task);
    } else {
        pr_info("[Transition] Transition done\n");
        xk_detach_auxiliary_kprobes();
        WRITE_ONCE(xk_state, XK_FLAGS_DONE);
    }

    return 0;
}

static void __exit consistency_exit(void) {
    pr_info("Xkernel consistency module unloaded\n");

    while (READ_ONCE(xk_state) == XK_FLAGS_PENDING) {
        // Wait for the transition being done or failed
        schedule();
    }
    
    if (READ_ONCE(xk_state) == XK_FLAGS_FAILED) {
        goto out;
    }
    
    BUG_ON(READ_ONCE(xk_state) != XK_FLAGS_DONE);

    // Since register_kprobe() is not allowed to be called in a stop_machine context, 
    // we need to attach the auxiliary kprobes here but don't enable them.
    xk_disable_auxiliary_kprobes();
    xk_attach_auxiliary_kprobes(false);
    
    stop_machine(xk_check_stacks, (void *)xk_state, NULL);
    
    if (xk_is_auxiliary_kprobes_on()) {
        WRITE_ONCE(xk_state, XK_FLAGS_REVERSE_PENDING);
        pr_info("[Reverse Transition] Waiting for reverse transition to be done or failed\n");
        wake_up_process(daemon_task);
        while (READ_ONCE(xk_state) == XK_FLAGS_REVERSE_PENDING) {
            // Wait for the reverse transition being done or failed
            schedule();
        }
    } else {
        pr_info("[Reverse Transition] Reverse transition done\n");
        xk_detach_auxiliary_kprobes();
        WRITE_ONCE(xk_state, XK_FLAGS_REVERSE_DONE);
    }

out:
    if (daemon_task) {
        kthread_stop(daemon_task);
        daemon_task = NULL;
    }
}

module_init(consistency_init);
module_exit(consistency_exit);