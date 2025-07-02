#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kprobes.h>
#include <linux/string.h>

// 宏定义结构体
struct macro_definition {
    char name[64];
    char definition[256];
    char *constants[10];  // 宏中使用的常量
    int constant_count;
};

// 分析配置
struct analysis_config {
    char function_name[64];
    struct macro_definition macro;
    unsigned long function_addr;
    unsigned char *function_code;
    int code_size;
};

static struct kprobe kp;
static struct analysis_config config;

// 预定义的宏常量模式
struct constant_pattern {
    unsigned int value;
    char *name;
    char *description;
};

static struct constant_pattern common_constants[] = {
    {1024, "1024", "Capacity scaling factor"},
    {1280, "1280", "Utilization scaling factor"},
    {256, "256", "Power of 2 scaling"},
    {512, "512", "Power of 2 scaling"},
    {2048, "2048", "Power of 2 scaling"},
    {4096, "4096", "Power of 2 scaling"},
    {8192, "8192", "Power of 2 scaling"},
    {16384, "16384", "Power of 2 scaling"},
    {32768, "32768", "Power of 2 scaling"},
    {65536, "65536", "Power of 2 scaling"},
    {0, NULL, NULL}
};

// 指令模式结构体
struct instruction_pattern {
    char *name;
    unsigned char pattern[8];
    int pattern_len;
    char *description;
    char *assembly_format;
};

static struct instruction_pattern instruction_patterns[] = {
    {"LEA_MUL_5", {0x48, 0x8d, 0x04, 0x89}, 4, "LEA instruction for multiplication by 5", "lea (%%rcx,%%rcx,4),%%rax"},
    {"SHL_256", {0x48, 0xc1, 0xe0, 0x08}, 4, "Shift left by 8 (multiply by 256)", "shl $0x8,%%rax"},
    {"MOV_1024", {0xb8, 0x00, 0x04, 0x00, 0x00}, 5, "Move immediate 1024", "mov $0x400,%%eax"},
    {"CMP_REG", {0x48, 0x39}, 2, "Compare registers", "cmp %%rax,%%rcx"},
    {"CMP_IMM", {0x39}, 1, "Compare with immediate", "cmp %%rax,%%rcx"},
    {"IMUL_REG", {0x69}, 1, "Signed multiply", "imul %%eax,%%r8d"},
    {"IMUL_IMM", {0x6b}, 1, "Signed multiply with immediate", "imul $imm,%%reg"},
    {"JMP_LESS", {0x0f, 0x8c}, 2, "Jump if less", "jl target"},
    {"JMP_GREATER_EQUAL", {0x0f, 0x8d}, 2, "Jump if greater or equal", "jge target"},
    {"JMP_BELOW", {0x0f, 0x82}, 2, "Jump if below", "jb target"},
    {"JMP_ABOVE_EQUAL", {0x0f, 0x83}, 2, "Jump if above or equal", "jae target"},
    {NULL, {0}, 0, NULL, NULL}
};

// 函数：解析宏定义
static int parse_macro_definition(const char *macro_def, struct macro_definition *macro) {
    char *def_copy = kmalloc(strlen(macro_def) + 1, GFP_KERNEL);
    if (!def_copy) return -ENOMEM;
    
    strcpy(def_copy, macro_def);
    
    // 提取宏名
    char *name_end = strchr(def_copy, '(');
    if (name_end) {
        int name_len = name_end - def_copy;
        strncpy(macro->name, def_copy, name_len);
        macro->name[name_len] = '\0';
    } else {
        strcpy(macro->name, "unknown");
    }
    
    // 提取宏定义
    char *def_start = strchr(def_copy, ')');
    if (def_start) {
        def_start++; // 跳过 ')'
        while (*def_start == ' ' || *def_start == '\t') def_start++;
        strcpy(macro->definition, def_start);
    } else {
        strcpy(macro->definition, macro_def);
    }
    
    // 查找常量
    macro->constant_count = 0;
    for (int i = 0; common_constants[i].value != 0; i++) {
        char value_str[16];
        snprintf(value_str, sizeof(value_str), "%u", common_constants[i].value);
        if (strstr(macro->definition, value_str)) {
            macro->constants[macro->constant_count++] = common_constants[i].name;
        }
    }
    
    kfree(def_copy);
    return 0;
}

// 函数：查找指令模式
static int find_instruction_patterns(unsigned char *code, int code_size, 
                                   struct instruction_pattern *patterns, int pattern_count) {
    int found_count = 0;
    
    for (int i = 0; i < code_size - 8; i++) {
        for (int p = 0; p < pattern_count; p++) {
            if (patterns[p].name == NULL) continue;
            
            int match = 1;
            for (int j = 0; j < patterns[p].pattern_len; j++) {
                if (code[i + j] != patterns[p].pattern[j]) {
                    match = 0;
                    break;
                }
            }
            
            if (match) {
                printk(KERN_INFO "找到指令模式 '%s' 在偏移 %d (0x%lx): ", 
                       patterns[p].name, i, config.function_addr + i);
                
                // 打印机器码
                for (int k = 0; k < patterns[p].pattern_len; k++) {
                    printk(KERN_INFO "%02x ", code[i + k]);
                }
                printk(KERN_INFO "- %s\n", patterns[p].description);
                
                found_count++;
            }
        }
    }
    
    return found_count;
}

// 函数：查找常量
static int find_constants(unsigned char *code, int code_size) {
    int found_count = 0;
    
    for (int i = 0; i < code_size - 4; i++) {
        for (int c = 0; common_constants[c].value != 0; c++) {
            unsigned int imm32 = *(unsigned int *)(&code[i]);
            if (imm32 == common_constants[c].value) {
                printk(KERN_INFO "找到常量 %s (%u) 在偏移 %d (0x%lx): ", 
                       common_constants[c].name, common_constants[c].value, 
                       i, config.function_addr + i);
                
                // 打印机器码
                for (int k = 0; k < 4; k++) {
                    printk(KERN_INFO "%02x ", code[i + k]);
                }
                printk(KERN_INFO "- %s\n", common_constants[c].description);
                
                found_count++;
            }
        }
    }
    
    return found_count;
}

// 函数：分析宏展开
static void analyze_macro_expansion(void) {
    printk(KERN_INFO "=== 通用宏汇编分析工具 ===\n");
    printk(KERN_INFO "函数名: %s\n", config.function_name);
    printk(KERN_INFO "函数地址: 0x%lx\n", config.function_addr);
    printk(KERN_INFO "宏名: %s\n", config.macro.name);
    printk(KERN_INFO "宏定义: %s\n", config.macro.definition);
    printk(KERN_INFO "宏中使用的常量: ");
    
    for (int i = 0; i < config.macro.constant_count; i++) {
        printk(KERN_INFO "%s ", config.macro.constants[i]);
    }
    printk(KERN_INFO "\n\n");
    
    // 查找指令模式
    printk(KERN_INFO "=== 查找指令模式 ===\n");
    int pattern_count = 0;
    while (instruction_patterns[pattern_count].name != NULL) pattern_count++;
    
    int found_patterns = find_instruction_patterns(config.function_code, config.code_size, 
                                                  instruction_patterns, pattern_count);
    printk(KERN_INFO "找到 %d 个指令模式\n\n", found_patterns);
    
    // 查找常量
    printk(KERN_INFO "=== 查找常量 ===\n");
    int found_constants = find_constants(config.function_code, config.code_size);
    printk(KERN_INFO "找到 %d 个常量\n\n", found_constants);
    
    // 分析宏展开
    printk(KERN_INFO "=== 宏展开分析 ===\n");
    printk(KERN_INFO "宏 %s 的可能汇编展开:\n", config.macro.name);
    
    // 根据宏定义和找到的模式生成可能的汇编展开
    if (strstr(config.macro.definition, "1280") && strstr(config.macro.definition, "1024")) {
        printk(KERN_INFO "检测到 fits_capacity 类型的宏:\n");
        printk(KERN_INFO "1. 计算第一个参数 * 1280 (优化版本):\n");
        printk(KERN_INFO "   lea (%%rcx,%%rcx,4),%%rax    # rax = rcx * 5\n");
        printk(KERN_INFO "   shl $0x8,%%rax             # rax = rax * 256 (总共乘以 1280)\n\n");
        
        printk(KERN_INFO "2. 计算第二个参数 * 1024:\n");
        printk(KERN_INFO "   mov $0x400,%%eax           # eax = 1024\n");
        printk(KERN_INFO "   imul %%eax,%%r8d            # r8d = capacity * 1024\n\n");
        
        printk(KERN_INFO "3. 比较操作:\n");
        printk(KERN_INFO "   cmp %%rax,%%r8d             # 比较两个结果\n\n");
        
        printk(KERN_INFO "4. 条件跳转:\n");
        printk(KERN_INFO "   jl macro_true              # 根据比较结果跳转\n");
        printk(KERN_INFO "   # 否则继续执行假分支\n\n");
    }
    
    // 打印完整的函数代码（用于调试）
    printk(KERN_INFO "=== 函数完整机器码 (前200字节) ===\n");
    for (int i = 0; i < 200 && i < config.code_size; i++) {
        if (i % 16 == 0) {
            printk(KERN_INFO "\n%04x: ", i);
        }
        printk(KERN_INFO "%02x ", config.function_code[i]);
    }
    printk(KERN_INFO "\n\n");
}

// 函数：初始化分析配置
static int init_analysis_config(const char *function_name, const char *macro_def) {
    strcpy(config.function_name, function_name);
    
    // 解析宏定义
    if (parse_macro_definition(macro_def, &config.macro) < 0) {
        printk(KERN_ERR "Failed to parse macro definition\n");
        return -1;
    }
    
    return 0;
}

// 函数：执行分析
static int perform_analysis(const char *function_name, const char *macro_def) {
    // 初始化配置
    if (init_analysis_config(function_name, macro_def) < 0) {
        return -1;
    }
    
    // 设置 kprobe
    memset(&kp, 0, sizeof(kp));
    kp.symbol_name = function_name;
    
    // 注册 kprobe
    int ret = register_kprobe(&kp);
    if (ret < 0) {
        printk(KERN_ERR "Failed to register kprobe for %s: %d\n", function_name, ret);
        return ret;
    }
    
    // 获取函数信息
    config.function_addr = (unsigned long)kp.addr;
    config.function_code = (unsigned char *)config.function_addr;
    config.code_size = 400; // 分析前400字节
    
    // 执行分析
    analyze_macro_expansion();
    
    // 清理
    unregister_kprobe(&kp);
    
    return 0;
}

static int __init generic_macro_analyzer_init(void) {
    printk(KERN_INFO "=== 通用宏汇编分析工具启动 ===\n");
    
    // 示例：分析 select_idle_capacity 函数中的 fits_capacity 宏
    const char *function_name = "select_idle_capacity";
    const char *macro_def = "fits_capacity(cap, max) ((cap) * 1280 < (max) * 1024)";
    
    printk(KERN_INFO "分析函数: %s\n", function_name);
    printk(KERN_INFO "分析宏: %s\n", macro_def);
    
    int ret = perform_analysis(function_name, macro_def);
    
    if (ret == 0) {
        printk(KERN_INFO "分析完成\n");
    } else {
        printk(KERN_ERR "分析失败: %d\n", ret);
    }
    
    return 0;
}

static void __exit generic_macro_analyzer_exit(void) {
    printk(KERN_INFO "通用宏汇编分析工具卸载\n");
}

module_init(generic_macro_analyzer_init);
module_exit(generic_macro_analyzer_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Generic macro assembly analyzer"); 