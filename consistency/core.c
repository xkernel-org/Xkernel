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

static int pid = 0;
module_param(pid, int, 0660);
MODULE_PARM_DESC(pid, "Userspace PID to notify");

LIST_HEAD(xk_target_functions);

#define MAX_STACK_ENTRIES 100
static DEFINE_PER_CPU(unsigned long[MAX_STACK_ENTRIES], xk_stack_entries);

#define INTERVAL_MS 1
#define TIMEOUT_TIMES 1000

static struct task_struct *daemon_task = NULL;
static struct sock *nl_sk = NULL;

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

static int init_netlink(void) {
    struct netlink_kernel_cfg cfg = {
        .input = NULL,
    };

    nl_sk = netlink_kernel_create(&init_net, NETLINK_USERSOCK, &cfg);
    if (IS_ERR(nl_sk)) {
        pr_err("Failed to create netlink socket\n");
        return PTR_ERR(nl_sk);
    }

    return 0;
}

static void cleanup_netlink(void) {
    if (nl_sk) {
        netlink_kernel_release(nl_sk);
        nl_sk = NULL;
    }
    return;
}

static void __xk_notify_usr(char *msg) {
    struct sk_buff *skb;
    struct nlmsghdr *nlh;
    int msg_size = strlen(msg) + 1;

    // 1. Allocate a new netlink message buffer
    skb = nlmsg_new(msg_size, GFP_KERNEL);
    if (!skb) {
        pr_err("Failed to allocate skb\n");
        return;
    }

    // 2. Add the netlink message header
    nlh = nlmsg_put(skb, 0, 0, NLMSG_DONE, msg_size, 0);
    
    // 3. Copy your message payload
    memcpy(nlmsg_data(nlh), msg, msg_size);

    // 4. Send the unicast message to the specific PID
    // Or use nlmsg_multicast() to send to a group
    nlmsg_unicast(nl_sk, skb, pid);
}

static void xk_enable_ir_kprobes(void) {
    __xk_notify_usr("1");
}

static void xk_disable_ir_kprobes(void) {
    __xk_notify_usr("0");
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

static int xk_check_stacks(void *data) {
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
        // There are related functions being executed, so we need to attach Guard/Unguard Kprobes to all related functions.
        pr_info("Attaching Auxiliary Kprobes to related functions\n");
        if (xk_attach_auxiliary_kprobes()) {
            pr_err("Failed to attach Auxiliary Kprobes\n");
            return -EINVAL;
        }
    } else {
        // Notify userspace to enable Instruction Rewriting Kprobes
        xk_enable_ir_kprobes();
        pr_info("Notified userspace to enable Instruction Rewriting Kprobes\n");
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

            // Initialize the kprobe structures
            xk_init_guard_kp(func);

            INIT_LIST_HEAD(&func->list);
            list_add_tail(&func->list, &xk_target_functions);

            printk("Added target function %s at 0x%lx with offset 0x%lx and size 0x%lx\n", func->name, func->address, func->offset, func->size);
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
    int ret = 0;

    while (!kthread_should_stop()) {

        if (xk_refcount() == 0) {
            // It's time to detach the auxiliary kprobes
            xk_detach_auxiliary_kprobes();
            pr_info("Detached Auxiliary Kprobes by daemon\n");
            break;
        }

        schedule_timeout(msecs_to_jiffies(INTERVAL_MS));
        if (times++ > TIMEOUT_TIMES) {
            pr_err("Daemon timeout\n");
            ret = -ETIMEDOUT;
            break;
        }
    }
    return ret;
}

static int __init consistency_init(void) {
    pr_info("Xkernel consistency module loaded\n");

    INIT_LIST_HEAD(&xk_target_functions);

    if (init_netlink()) {pr_err("Failed to init netlink\n"); return -1;}

    measure_stop_machine_overhead();
    
    daemon_task = kthread_create(daemon_main, NULL, "xkernel-daemon");
    if (IS_ERR(daemon_task)) {
        pr_err("Failed to create daemon task\n");
        return PTR_ERR(daemon_task);
    }
    
    if (xk_read_target_functions()) {pr_err("Failed to read target functions\n"); return -1;}

    stop_machine(xk_check_stacks, NULL, NULL);

    if (xk_refcount() > 0) {
        wake_up_process(daemon_task);
    } else {
        kthread_stop(daemon_task);
        daemon_task = NULL;
    }

    return 0;
}

static void __exit consistency_exit(void) {
    pr_info("Xkernel consistency module unloaded\n");
    xk_detach_auxiliary_kprobes();

    if (daemon_task) {
        kthread_stop(daemon_task);
        daemon_task = NULL;
    }

    cleanup_netlink();
}

module_init(consistency_init);
module_exit(consistency_exit);
