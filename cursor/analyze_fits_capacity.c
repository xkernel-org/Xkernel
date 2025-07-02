#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kprobes.h>

static struct kprobe kp = {
    .symbol_name = "select_idle_capacity",
};

static int __init analyze_fits_capacity_init(void)
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
    
    // 分析 fits_capacity 的汇编展开
    // fits_capacity(util, capacity) = (util * 1280) < (capacity * 1024)
    
    printk(KERN_INFO "Analyzing fits_capacity macro assembly expansion:\n");
    printk(KERN_INFO "Macro: fits_capacity(util, capacity) = (util * 1280) < (capacity * 1024)\n");
    
    // 查找 1024 立即数 (0x400)
    for (i = 0; i < 300; i++) {
        if (i + 3 < 300) {
            unsigned int imm32 = *(unsigned int *)(&code[i]);
            if (imm32 == 1024) {
                printk(KERN_INFO "Found immediate 1024 (0x400) at offset %d (0x%lx)\n", 
                       i, func_addr + i);
                
                // 打印周围的代码来分析指令序列
                printk(KERN_INFO "Context around 1024 immediate:\n");
                int j;
                for (j = i - 20; j <= i + 20; j++) {
                    if (j >= 0 && j < 300) {
                        if (j == i) {
                            printk(KERN_INFO "[%02x%02x%02x%02x] ", 
                                   code[j], code[j+1], code[j+2], code[j+3]);
                            j += 3; // 跳过已打印的字节
                        } else {
                            printk(KERN_INFO "%02x ", code[j]);
                        }
                    }
                }
                printk(KERN_INFO "\n");
            }
        }
    }
    
    // 查找 1280 立即数 (0x500)
    for (i = 0; i < 300; i++) {
        if (i + 3 < 300) {
            unsigned int imm32 = *(unsigned int *)(&code[i]);
            if (imm32 == 1280) {
                printk(KERN_INFO "Found immediate 1280 (0x500) at offset %d (0x%lx)\n", 
                       i, func_addr + i);
                
                // 打印周围的代码
                printk(KERN_INFO "Context around 1280 immediate:\n");
                int j;
                for (j = i - 20; j <= i + 20; j++) {
                    if (j >= 0 && j < 300) {
                        if (j == i) {
                            printk(KERN_INFO "[%02x%02x%02x%02x] ", 
                                   code[j], code[j+1], code[j+2], code[j+3]);
                            j += 3;
                        } else {
                            printk(KERN_INFO "%02x ", code[j]);
                        }
                    }
                }
                printk(KERN_INFO "\n");
            }
        }
    }
    
    // 分析比较指令序列
    printk(KERN_INFO "\nAnalyzing comparison instruction sequences:\n");
    
    for (i = 0; i < 300; i++) {
        // 查找 cmp 指令
        if (code[i] == 0x39 || code[i] == 0x3b) {
            printk(KERN_INFO "Found cmp instruction at offset %d (0x%lx): 0x%02x\n", 
                   i, func_addr + i, code[i]);
            
            // 查找后续的条件跳转
            if (i + 2 < 300 && code[i+1] == 0x0f) {
                printk(KERN_INFO "  Followed by conditional jump: 0x%02x at offset %d\n", 
                       code[i+2], i+2);
            }
        }
    }
    
    // 特别分析偏移 92 附近的代码 (之前发现的 cmp 指令)
    printk(KERN_INFO "\nDetailed analysis around offset 92 (potential fits_capacity):\n");
    for (i = 85; i < 105; i++) {
        if (i % 16 == 0) {
            printk(KERN_INFO "\n%04x: ", i);
        }
        if (i == 92) {
            printk(KERN_INFO "[%02x]", code[i]);
        } else {
            printk(KERN_INFO "%02x ", code[i]);
        }
    }
    printk(KERN_INFO "\n");
    
    // 分析偏移 237 附近的代码 (1024 立即数位置)
    printk(KERN_INFO "\nDetailed analysis around offset 237 (1024 immediate):\n");
    for (i = 230; i < 250; i++) {
        if (i % 16 == 0) {
            printk(KERN_INFO "\n%04x: ", i);
        }
        if (i >= 237 && i <= 240) {
            printk(KERN_INFO "[%02x]", code[i]);
        } else {
            printk(KERN_INFO "%02x ", code[i]);
        }
    }
    printk(KERN_INFO "\n");
    
    unregister_kprobe(&kp);
    
    return 0;
}

static void __exit analyze_fits_capacity_exit(void)
{
    printk(KERN_INFO "analyze_fits_capacity module unloaded\n");
}

module_init(analyze_fits_capacity_init);
module_exit(analyze_fits_capacity_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Analyze fits_capacity macro assembly"); 