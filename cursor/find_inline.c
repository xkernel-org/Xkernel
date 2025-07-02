#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kprobes.h>

static struct kprobe kp = {
    .symbol_name = "select_idle_capacity",
};

static int __init find_inline_init(void)
{
    int ret;
    unsigned long func_addr;
    unsigned char *code;
    int i;
    
    ret = register_kprobe(&kp);
    if (ret < 0) {
        printk(KERN_INFO "Failed to register kprobe: %d\n", ret);
        return ret;
    }
    
    func_addr = (unsigned long)kp.addr;
    printk(KERN_INFO "select_idle_capacity function address: 0x%lx\n", func_addr);
    
    code = (unsigned char *)func_addr;
    
    // 查找可能的 util_fits_cpu 内联代码模式
    // 根据源代码，util_fits_cpu 调用应该在偏移 92 附近
    printk(KERN_INFO "Analyzing code around expected util_fits_cpu call (offset ~92):\n");
    
    for (i = 85; i < 110; i++) {
        if (i % 16 == 0) {
            printk(KERN_INFO "\n%04x: ", i);
        }
        printk(KERN_INFO "%02x ", code[i]);
    }
    printk(KERN_INFO "\n");
    
    // 查找函数调用
    printk(KERN_INFO "Function calls in select_idle_capacity:\n");
    for (i = 0; i < 200; i++) {
        if (code[i] == 0xe8) { // call 指令
            unsigned long call_target;
            int offset;
            
            offset = *(int *)(&code[i + 1]);
            call_target = func_addr + i + 5 + offset;
            
            printk(KERN_INFO "Call at offset %d (0x%lx): target 0x%lx\n", 
                   i, func_addr + i, call_target);
            
            // 尝试识别这个调用
            if (call_target == 0xffffffffa2d59a90) {
                printk(KERN_INFO "  -> This is uclamp_eff_value\n");
            } else if (call_target == 0xffffffffa345c5d0) {
                printk(KERN_INFO "  -> This is __bitmap_and\n");
            } else if (call_target == 0xffffffffa3465910) {
                printk(KERN_INFO "  -> This is _find_next_bit\n");
            } else {
                printk(KERN_INFO "  -> Unknown function\n");
            }
        }
    }
    
    unregister_kprobe(&kp);
    
    // 尝试查找 util_fits_cpu 的符号（应该失败）
    kp.symbol_name = "util_fits_cpu";
    ret = register_kprobe(&kp);
    if (ret < 0) {
        printk(KERN_INFO "util_fits_cpu not found as separate symbol (inline function)\n");
    } else {
        printk(KERN_INFO "util_fits_cpu found at: 0x%lx\n", (unsigned long)kp.addr);
        unregister_kprobe(&kp);
    }
    
    return 0;
}

static void __exit find_inline_exit(void)
{
    printk(KERN_INFO "find_inline module unloaded\n");
}

module_init(find_inline_init);
module_exit(find_inline_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Find inline util_fits_cpu"); 