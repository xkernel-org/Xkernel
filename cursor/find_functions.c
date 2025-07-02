#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kprobes.h>

static struct kprobe kp = {
    .symbol_name = "select_idle_capacity",
};

static int __init find_functions_init(void)
{
    int ret;
    
    // 注册 kprobe 来查找 select_idle_capacity 函数
    ret = register_kprobe(&kp);
    if (ret < 0) {
        printk(KERN_INFO "Failed to register kprobe for select_idle_capacity: %d\n", ret);
    } else {
        printk(KERN_INFO "select_idle_capacity found at address: 0x%lx\n", (unsigned long)kp.addr);
        unregister_kprobe(&kp);
    }
    
    // 尝试查找 task_fits_cpu 函数
    kp.symbol_name = "task_fits_cpu";
    ret = register_kprobe(&kp);
    if (ret < 0) {
        printk(KERN_INFO "Failed to register kprobe for task_fits_cpu: %d\n", ret);
    } else {
        printk(KERN_INFO "task_fits_cpu found at address: 0x%lx\n", (unsigned long)kp.addr);
        unregister_kprobe(&kp);
    }
    
    // 尝试查找 asym_fits_cpu 函数
    kp.symbol_name = "asym_fits_cpu";
    ret = register_kprobe(&kp);
    if (ret < 0) {
        printk(KERN_INFO "Failed to register kprobe for asym_fits_cpu: %d\n", ret);
    } else {
        printk(KERN_INFO "asym_fits_cpu found at address: 0x%lx\n", (unsigned long)kp.addr);
        unregister_kprobe(&kp);
    }
    
    return 0;
}

static void __exit find_functions_exit(void)
{
    printk(KERN_INFO "find_functions module unloaded\n");
}

module_init(find_functions_init);
module_exit(find_functions_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Find function addresses in kernel"); 