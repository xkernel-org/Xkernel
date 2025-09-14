#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kprobes.h>
#include <linux/sched.h>

#define FUNCTION_OFFSET 0x148

static struct kprobe kp = {
    .symbol_name    = "throtl_pending_timer_fn",
    .offset         = FUNCTION_OFFSET,
};

static int pre_handler(struct kprobe *p, struct pt_regs *regs)
{
    printk("pre_handler\n");
    // Print the current PC register
#if defined(__x86_64__)
    printk("Current PC (RIP): 0x%lx\n", regs->ip);
#elif defined(__aarch64__)
    printk("Current PC (PC): 0x%llx\n", regs->pc);
#else
    printk("Current PC: unknown architecture\n");
#endif
    
    return 0;
}

static void post_handler(struct kprobe *p, struct pt_regs *regs, unsigned long flags)
{
    printk("post_handler\n");
}

static int __init kprobe_init(void)
{
    int ret;
    
    kp.pre_handler = pre_handler;
    // kp.pre_handler = NULL;
    kp.post_handler = post_handler;
    
    ret = register_kprobe(&kp);
    if (ret < 0) {
        printk(KERN_ERR "register kprobe failed, offset: 0x%x, error: %d\n",
               FUNCTION_OFFSET, ret);
        return ret;
    }
    
    printk(KERN_INFO "kprobe registered, offset: 0x%x\n",
           FUNCTION_OFFSET);
    return 0;
}

static void __exit kprobe_exit(void)
{
    unregister_kprobe(&kp);
    printk(KERN_INFO "kprobe unregistered, offset: 0x%x\n",
           FUNCTION_OFFSET);
}

module_init(kprobe_init);
module_exit(kprobe_exit);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Raw kprobe");
MODULE_AUTHOR("Zhongjie");
