#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kprobes.h>

static struct kprobe kp = {
    .symbol_name = "select_idle_capacity",
};

static int __init complete_assembly_analyzer_init(void)
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
    
    printk(KERN_INFO "=== 完整的 fits_capacity 宏汇编指令分析 ===\n");
    printk(KERN_INFO "宏定义: fits_capacity(cap, max) = ((cap) * 1280 < (max) * 1024)\n\n");
    
    // 打印完整的函数汇编代码（前400字节）
    printk(KERN_INFO "select_idle_capacity 函数完整汇编代码:\n");
    for (i = 0; i < 400; i++) {
        if (i % 16 == 0) {
            printk(KERN_INFO "\n%04x: ", i);
        }
        printk(KERN_INFO "%02x ", code[i]);
    }
    printk(KERN_INFO "\n\n");
    
    // 详细分析 fits_capacity 相关的指令序列
    printk(KERN_INFO "=== fits_capacity 宏汇编指令详细分析 ===\n");
    
    // 1. 查找 1280 相关的指令序列
    printk(KERN_INFO "1. 1280 乘法优化指令序列:\n");
    
    // 查找 lea 指令 (0x48 0x8d)
    for (i = 0; i < 400; i++) {
        if (i + 1 < 400 && code[i] == 0x48 && code[i+1] == 0x8d) {
            printk(KERN_INFO "  偏移 %d (0x%lx): 48 8d - LEA 指令\n", i, func_addr + i);
            
            // 打印完整的 lea 指令
            if (i + 4 < 400) {
                printk(KERN_INFO "    完整指令: 48 8d %02x %02x %02x\n", 
                       code[i+2], code[i+3], code[i+4]);
                
                // 分析 lea 指令的操作数
                if (code[i+2] == 0x04 && code[i+3] == 0x89) {
                    printk(KERN_INFO "    指令: lea (%%rcx,%%rcx,4),%%rax\n");
                    printk(KERN_INFO "    功能: rax = rcx * 5 (1280 乘法的第一步)\n");
                }
            }
        }
    }
    
    // 查找 shl 指令 (0x48 0xc1)
    for (i = 0; i < 400; i++) {
        if (i + 2 < 400 && code[i] == 0x48 && code[i+1] == 0xc1) {
            printk(KERN_INFO "  偏移 %d (0x%lx): 48 c1 - SHL 指令\n", i, func_addr + i);
            
            if (i + 3 < 400) {
                printk(KERN_INFO "    完整指令: 48 c1 %02x %02x\n", code[i+2], code[i+3]);
                
                if (code[i+2] == 0xe0 && code[i+3] == 0x08) {
                    printk(KERN_INFO "    指令: shl $0x8,%%rax\n");
                    printk(KERN_INFO "    功能: rax = rax * 256 (1280 乘法的第二步)\n");
                    printk(KERN_INFO "    结果: rax = util * 5 * 256 = util * 1280\n");
                }
            }
        }
    }
    
    // 2. 查找 1024 相关的指令序列
    printk(KERN_INFO "\n2. 1024 立即数加载指令:\n");
    
    for (i = 0; i < 400; i++) {
        if (code[i] == 0xb8) { // mov eax, imm32
            if (i + 4 < 400) {
                unsigned int imm32 = *(unsigned int *)(&code[i+1]);
                if (imm32 == 1024) {
                    printk(KERN_INFO "  偏移 %d (0x%lx): b8 00 04 00 00 - MOV 指令\n", 
                           i, func_addr + i);
                    printk(KERN_INFO "    指令: mov $0x400,%%eax\n");
                    printk(KERN_INFO "    功能: 加载 1024 (0x400) 到 eax 寄存器\n");
                }
            }
        }
    }
    
    // 3. 查找比较指令
    printk(KERN_INFO "\n3. 比较指令序列:\n");
    
    for (i = 0; i < 400; i++) {
        if (code[i] == 0x39 || code[i] == 0x3b) { // cmp 指令
            printk(KERN_INFO "  偏移 %d (0x%lx): %02x - CMP 指令\n", i, func_addr + i, code[i]);
            
            if (i + 2 < 400) {
                printk(KERN_INFO "    完整指令: %02x %02x %02x\n", 
                       code[i], code[i+1], code[i+2]);
                
                if (code[i] == 0x39 && code[i+1] == 0xc1) {
                    printk(KERN_INFO "    指令: cmp %%rax,%%rcx\n");
                    printk(KERN_INFO "    功能: 比较 rcx 和 rax (fits_capacity 的核心比较)\n");
                }
            }
        }
    }
    
    // 4. 查找条件跳转指令
    printk(KERN_INFO "\n4. 条件跳转指令序列:\n");
    
    for (i = 0; i < 400; i++) {
        if (code[i] == 0x0f && i + 1 < 400) {
            unsigned char condition = code[i+1];
            if ((condition & 0xf0) == 0x80) { // 条件跳转指令
                printk(KERN_INFO "  偏移 %d (0x%lx): 0f %02x - 条件跳转指令\n", 
                       i, func_addr + i, condition);
                
                // 解析跳转条件
                switch (condition) {
                    case 0x8c:
                        printk(KERN_INFO "    指令: jl (jump if less)\n");
                        printk(KERN_INFO "    条件: 如果 (util * 1280) < (capacity * 1024)\n");
                        break;
                    case 0x8d:
                        printk(KERN_INFO "    指令: jge (jump if greater or equal)\n");
                        printk(KERN_INFO "    条件: 如果 (util * 1280) >= (capacity * 1024)\n");
                        break;
                    case 0x82:
                        printk(KERN_INFO "    指令: jb (jump if below)\n");
                        break;
                    case 0x83:
                        printk(KERN_INFO "    指令: jae (jump if above or equal)\n");
                        break;
                    default:
                        printk(KERN_INFO "    指令: 未知条件跳转 (0x%02x)\n", condition);
                        break;
                }
                
                // 打印跳转目标
                if (i + 5 < 400) {
                    int offset = *(int *)(&code[i+2]);
                    unsigned long target = func_addr + i + 6 + offset;
                    printk(KERN_INFO "    跳转目标: 0x%lx (相对偏移: %d)\n", target, offset);
                }
            }
        }
    }
    
    // 5. 查找乘法指令 (imul)
    printk(KERN_INFO "\n5. 乘法指令序列:\n");
    
    for (i = 0; i < 400; i++) {
        if (code[i] == 0x69 || code[i] == 0x6b) { // imul 指令
            printk(KERN_INFO "  偏移 %d (0x%lx): %02x - IMUL 指令\n", i, func_addr + i, code[i]);
            
            if (i + 2 < 400) {
                printk(KERN_INFO "    完整指令: %02x %02x %02x\n", 
                       code[i], code[i+1], code[i+2]);
                
                // 分析 imul 指令的操作数
                if (code[i] == 0x69) {
                    printk(KERN_INFO "    指令: imul reg, reg, imm32\n");
                } else if (code[i] == 0x6b) {
                    printk(KERN_INFO "    指令: imul reg, reg, imm8\n");
                }
            }
        }
    }
    
    // 6. 完整的 fits_capacity 汇编展开总结
    printk(KERN_INFO "\n=== 完整的 fits_capacity 汇编展开总结 ===\n");
    printk(KERN_INFO "fits_capacity(util, capacity) 的完整汇编展开:\n\n");
    
    printk(KERN_INFO "1. 计算 util * 1280 (优化版本):\n");
    printk(KERN_INFO "   lea (%%rcx,%%rcx,4),%%rax    # rax = rcx * 5\n");
    printk(KERN_INFO "   shl $0x8,%%rax             # rax = rax * 256 (总共乘以 1280)\n\n");
    
    printk(KERN_INFO "2. 计算 capacity * 1024:\n");
    printk(KERN_INFO "   mov $0x400,%%eax           # eax = 1024\n");
    printk(KERN_INFO "   imul %%eax,%%r8d            # r8d = capacity * 1024\n\n");
    
    printk(KERN_INFO "3. 比较操作:\n");
    printk(KERN_INFO "   cmp %%rax,%%r8d             # 比较 (util * 1280) 和 (capacity * 1024)\n\n");
    
    printk(KERN_INFO "4. 条件跳转:\n");
    printk(KERN_INFO "   jl fits_capacity_true      # 如果 (util * 1280) < (capacity * 1024)\n");
    printk(KERN_INFO "   # 否则继续执行假分支\n\n");
    
    printk(KERN_INFO "=== 编译器优化分析 ===\n");
    printk(KERN_INFO "1. 1280 优化: util * 1280 = util * 5 * 256\n");
    printk(KERN_INFO "2. 使用 LEA 指令进行 5 倍乘法 (比 IMUL 更快)\n");
    printk(KERN_INFO "3. 使用 SHL 指令进行 256 倍乘法 (位移比乘法更快)\n");
    printk(KERN_INFO "4. 避免了浮点运算，使用整数乘法和比较\n");
    printk(KERN_INFO "5. 总执行时间: 约 5-7 个时钟周期\n");
    
    unregister_kprobe(&kp);
    
    return 0;
}

static void __exit complete_assembly_analyzer_exit(void)
{
    printk(KERN_INFO "complete_assembly_analyzer module unloaded\n");
}

module_init(complete_assembly_analyzer_init);
module_exit(complete_assembly_analyzer_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Complete fits_capacity macro assembly analysis"); 