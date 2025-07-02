#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kprobes.h>

static struct kprobe kp = {
    .symbol_name = "select_idle_capacity",
};

static int __init find_fits_capacity_init(void)
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
    
    // 分析 fits_capacity 宏的汇编展开
    // fits_capacity(util, capacity) 展开为: (util) * 1280 < (capacity) * 1024
    // 在 x86_64 汇编中，这通常涉及乘法、比较和条件跳转指令
    
    printk(KERN_INFO "Searching for fits_capacity macro expansion patterns...\n");
    printk(KERN_INFO "Pattern: (util * 1280) < (capacity * 1024)\n");
    printk(KERN_INFO "1280 = 0x500, 1024 = 0x400\n");
    
    // 查找可能的乘法指令模式
    // imul 指令的常见模式
    for (i = 0; i < 300; i++) {
        // 查找 imul 指令 (0x69 或 0x6b)
        if (code[i] == 0x69 || code[i] == 0x6b) {
            printk(KERN_INFO "Found imul instruction at offset %d (0x%lx)\n", 
                   i, func_addr + i);
            
            // 打印周围的代码
            int j;
            printk(KERN_INFO "Context around imul:\n");
            for (j = i - 10; j <= i + 10; j++) {
                if (j >= 0 && j < 300) {
                    printk(KERN_INFO "%02x ", code[j]);
                }
            }
            printk(KERN_INFO "\n");
        }
        
        // 查找 mov 指令后跟立即数 (可能是加载 1280 或 1024)
        if (code[i] == 0x48 && code[i+1] == 0xb8) { // mov rax, imm64
            unsigned long imm = *(unsigned long *)(&code[i+2]);
            if (imm == 1280 || imm == 1024) {
                printk(KERN_INFO "Found mov with immediate %lu at offset %d (0x%lx)\n", 
                       imm, i, func_addr + i);
            }
        }
        
        // 查找 cmp 指令 (0x39 或 0x3b)
        if (code[i] == 0x39 || code[i] == 0x3b) {
            printk(KERN_INFO "Found cmp instruction at offset %d (0x%lx)\n", 
                   i, func_addr + i);
        }
        
        // 查找条件跳转指令 (0x0f 后跟 0x8x)
        if (code[i] == 0x0f && (code[i+1] & 0xf0) == 0x80) {
            printk(KERN_INFO "Found conditional jump at offset %d (0x%lx), condition: 0x%02x\n", 
                   i, func_addr + i, code[i+1]);
        }
    }
    
    // 特别查找 fits_capacity 的完整模式
    printk(KERN_INFO "\nDetailed analysis of potential fits_capacity expansion:\n");
    
    // 查找 1280 (0x500) 的立即数
    for (i = 0; i < 300; i++) {
        if (i + 3 < 300) {
            unsigned int imm32 = *(unsigned int *)(&code[i]);
            if (imm32 == 1280) {
                printk(KERN_INFO "Found immediate 1280 at offset %d (0x%lx)\n", 
                       i, func_addr + i);
            }
        }
    }
    
    // 查找 1024 (0x400) 的立即数
    for (i = 0; i < 300; i++) {
        if (i + 3 < 300) {
            unsigned int imm32 = *(unsigned int *)(&code[i]);
            if (imm32 == 1024) {
                printk(KERN_INFO "Found immediate 1024 at offset %d (0x%lx)\n", 
                       i, func_addr + i);
            }
        }
    }
    
    unregister_kprobe(&kp);
    
    return 0;
}

static void __exit find_fits_capacity_exit(void)
{
    printk(KERN_INFO "find_fits_capacity module unloaded\n");
}

module_init(find_fits_capacity_init);
module_exit(find_fits_capacity_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Find fits_capacity macro assembly expansion"); 