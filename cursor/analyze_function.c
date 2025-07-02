#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kprobes.h>
#include <linux/uaccess.h>

// select_idle_capacity 函数的地址
#define SELECT_IDLE_CAPACITY_ADDR 0xffffffffa2d67170

static struct kprobe kp = {
    .symbol_name = "select_idle_capacity",
};

// 用于存储函数调用的结构
struct function_call_info {
    unsigned long caller_addr;
    unsigned long target_addr;
    char target_name[64];
};

static int __init analyze_function_init(void)
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
    
    // 尝试分析函数代码（注意：这需要内核内存访问权限）
    code = (unsigned char *)func_addr;
    
    // 打印前100字节的代码（用于调试）
    printk(KERN_INFO "First 100 bytes of select_idle_capacity:\n");
    for (i = 0; i < 100; i++) {
        if (i % 16 == 0) {
            printk(KERN_INFO "\n%04x: ", i);
        }
        printk(KERN_INFO "%02x ", code[i]);
    }
    printk(KERN_INFO "\n");
    
    unregister_kprobe(&kp);
    
    // 尝试查找调用 util_fits_cpu 的位置
    // 在 x86_64 中，函数调用通常使用 call 指令 (0xe8)
    printk(KERN_INFO "Searching for function calls in select_idle_capacity...\n");
    
    for (i = 0; i < 200; i++) {
        if (code[i] == 0xe8) { // call 指令
            unsigned long call_target;
            int offset;
            
            // 获取相对偏移
            offset = *(int *)(&code[i + 1]);
            call_target = func_addr + i + 5 + offset;
            
            printk(KERN_INFO "Found call instruction at offset %d, target: 0x%lx\n", 
                   i, call_target);
        }
    }
    
    return 0;
}

static void __exit analyze_function_exit(void)
{
    printk(KERN_INFO "analyze_function module unloaded\n");
}

module_init(analyze_function_init);
module_exit(analyze_function_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Analyze select_idle_capacity function"); 