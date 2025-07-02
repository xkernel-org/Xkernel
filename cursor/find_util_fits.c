#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kprobes.h>

static struct kprobe kp = {
    .symbol_name = "select_idle_capacity",
};

static int __init find_util_fits_init(void)
{
    int ret;
    unsigned long func_addr;
    unsigned char *code;
    int i;
    
    // 注册 kprobe 来获取函数地址
    ret = register_kprobe(&kp);
    if (ret < 0) {
        printk(KERN_INFO "Failed to register kprobe: %d\n", ret);
        return ret;
    }
    
    func_addr = (unsigned long)kp.addr;
    printk(KERN_INFO "select_idle_capacity function address: 0x%lx\n", func_addr);
    
    code = (unsigned char *)func_addr;
    
    // 查找所有函数调用
    printk(KERN_INFO "All function calls in select_idle_capacity:\n");
    for (i = 0; i < 300; i++) {
        if (code[i] == 0xe8) { // call 指令
            unsigned long call_target;
            int offset;
            
            offset = *(int *)(&code[i + 1]);
            call_target = func_addr + i + 5 + offset;
            
            printk(KERN_INFO "Call at offset %d (0x%lx): target 0x%lx\n", 
                   i, func_addr + i, call_target);
        }
    }
    
    unregister_kprobe(&kp);
    
    // 尝试查找 util_fits_cpu 的符号
    kp.symbol_name = "util_fits_cpu";
    ret = register_kprobe(&kp);
    if (ret < 0) {
        printk(KERN_INFO "util_fits_cpu not found as separate symbol (expected for inline function)\n");
    } else {
        printk(KERN_INFO "util_fits_cpu found at: 0x%lx\n", (unsigned long)kp.addr);
        unregister_kprobe(&kp);
    }
    
    return 0;
}

static void __exit find_util_fits_exit(void)
{
    printk(KERN_INFO "find_util_fits module unloaded\n");
}

module_init(find_util_fits_init);
module_exit(find_util_fits_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Find util_fits_cpu calls"); 