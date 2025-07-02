#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kprobes.h>
#include <linux/string.h>
#include <linux/slab.h>
#include <linux/string.h>

// 宏定义结构体
struct macro_definition {
    char name[64];
    char definition[256];
    char *parameters[10];  // 宏参数
    int param_count;
    char *constants[20];   // 宏中使用的常量
    int constant_count;
    char *operations[10];  // 宏中的操作
    int op_count;
};

// 汇编指令结构体
struct assembly_instruction {
    char *name;
    unsigned char pattern[16];
    int pattern_len;
    char *description;
    char *assembly_format;
    int clock_cycles;
};

// 分析结果结构体
struct analysis_result {
    struct macro_definition macro;
    struct assembly_instruction *found_instructions;
    int instruction_count;
    unsigned long *instruction_offsets;
    char *assembly_expansion;
    int total_clock_cycles;
};

// 分析配置
struct analysis_config {
    char function_name[64];
    struct macro_definition macro;
    unsigned long function_addr;
    unsigned char *function_code;
    int code_size;
    struct analysis_result result;
};

static struct kprobe kp;
static struct analysis_config config;

// 预定义的常量模式
struct constant_pattern {
    unsigned int value;
    char *name;
    char *description;
    char *hex_value;
};

static struct constant_pattern common_constants[] = {
    {1024, "1024", "Capacity scaling factor", "0x400"},
    {1280, "1280", "Utilization scaling factor", "0x500"},
    {256, "256", "Power of 2 scaling", "0x100"},
    {512, "512", "Power of 2 scaling", "0x200"},
    {2048, "2048", "Power of 2 scaling", "0x800"},
    {4096, "4096", "Power of 2 scaling", "0x1000"},
    {8192, "8192", "Power of 2 scaling", "0x2000"},
    {16384, "16384", "Power of 2 scaling", "0x4000"},
    {32768, "32768", "Power of 2 scaling", "0x8000"},
    {65536, "65536", "Power of 2 scaling", "0x10000"},
    {0, NULL, NULL, NULL}
};

// 预定义的汇编指令模式
static struct assembly_instruction instruction_patterns[] = {
    {"LEA_MUL_5", {0x48, 0x8d, 0x04, 0x89}, 4, "LEA instruction for multiplication by 5", "lea (%%rcx,%%rcx,4),%%rax", 1},
    {"LEA_MUL_3", {0x48, 0x8d, 0x04, 0x49}, 4, "LEA instruction for multiplication by 3", "lea (%%rcx,%%rcx,2),%%rax", 1},
    {"LEA_MUL_9", {0x48, 0x8d, 0x04, 0xc9}, 4, "LEA instruction for multiplication by 9", "lea (%%rcx,%%rcx,8),%%rax", 1},
    {"SHL_256", {0x48, 0xc1, 0xe0, 0x08}, 4, "Shift left by 8 (multiply by 256)", "shl $0x8,%%rax", 1},
    {"SHL_512", {0x48, 0xc1, 0xe0, 0x09}, 4, "Shift left by 9 (multiply by 512)", "shl $0x9,%%rax", 1},
    {"SHL_1024", {0x48, 0xc1, 0xe0, 0x0a}, 4, "Shift left by 10 (multiply by 1024)", "shl $0x0a,%%rax", 1},
    {"MOV_1024", {0xb8, 0x00, 0x04, 0x00, 0x00}, 5, "Move immediate 1024", "mov $0x400,%%eax", 1},
    {"MOV_1280", {0xb8, 0x00, 0x05, 0x00, 0x00}, 5, "Move immediate 1280", "mov $0x500,%%eax", 1},
    {"CMP_REG", {0x48, 0x39}, 2, "Compare registers", "cmp %%rax,%%rcx", 1},
    {"CMP_IMM", {0x39}, 1, "Compare with immediate", "cmp %%rax,%%rcx", 1},
    {"IMUL_REG", {0x69}, 1, "Signed multiply", "imul %%eax,%%r8d", 3},
    {"IMUL_IMM", {0x6b}, 1, "Signed multiply with immediate", "imul $imm,%%reg", 3},
    {"MUL_REG", {0x48, 0xf7}, 2, "Unsigned multiply", "mul %%rax", 3},
    {"JMP_LESS", {0x0f, 0x8c}, 2, "Jump if less", "jl target", 1},
    {"JMP_GREATER_EQUAL", {0x0f, 0x8d}, 2, "Jump if greater or equal", "jge target", 1},
    {"JMP_BELOW", {0x0f, 0x82}, 2, "Jump if below", "jb target", 1},
    {"JMP_ABOVE_EQUAL", {0x0f, 0x83}, 2, "Jump if above or equal", "jae target", 1},
    {"JMP_EQUAL", {0x0f, 0x84}, 2, "Jump if equal", "je target", 1},
    {"JMP_NOT_EQUAL", {0x0f, 0x85}, 2, "Jump if not equal", "jne target", 1},
    {"ADD_REG", {0x48, 0x01}, 2, "Add registers", "add %%rax,%%rcx", 1},
    {"SUB_REG", {0x48, 0x29}, 2, "Subtract registers", "sub %%rax,%%rcx", 1},
    {"AND_REG", {0x48, 0x21}, 2, "Bitwise AND", "and %%rax,%%rcx", 1},
    {"OR_REG", {0x48, 0x09}, 2, "Bitwise OR", "or %%rax,%%rcx", 1},
    {"XOR_REG", {0x48, 0x31}, 2, "Bitwise XOR", "xor %%rax,%%rcx", 1},
    {NULL, {0}, 0, NULL, NULL, 0}
};

static char user_function_name[128] = "select_idle_capacity";
static char user_macro_def[512] = "fits_capacity(cap, max) ((cap) * 1280 < (max) * 1024)";

// 使用数组参数来避免特殊字符解析问题
static int macro_def_parts = 0;
static char macro_def_part1[128] = "util_fits_cpu(util, min, max, cpu)";
static char macro_def_part2[128] = "((util) >= (min) && (util) <= (max))";

module_param_string(function_name, user_function_name, sizeof(user_function_name), 0644);
MODULE_PARM_DESC(function_name, "Function name to analyze");

module_param_string(macro_def1, macro_def_part1, sizeof(macro_def_part1), 0644);
MODULE_PARM_DESC(macro_def1, "First part of macro definition (name and parameters)");

module_param_string(macro_def2, macro_def_part2, sizeof(macro_def_part2), 0644);
MODULE_PARM_DESC(macro_def2, "Second part of macro definition (expression)");

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
    
    // 提取参数
    if (name_end) {
        char *param_start = name_end + 1;
        char *param_end = strchr(param_start, ')');
        if (param_end) {
            *param_end = '\0';
            macro->param_count = 0;
            char *p = param_start;
            while (*p) {
                // 跳过前导空格
                while (*p == ' ') p++;
                if (!*p) break;
                char *q = strchr(p, ',');
                int len = q ? (q - p) : strlen(p);
                // 去除末尾空格
                while (len > 0 && p[len-1] == ' ') len--;
                macro->parameters[macro->param_count] = kmalloc(len+1, GFP_KERNEL);
                strncpy(macro->parameters[macro->param_count], p, len);
                macro->parameters[macro->param_count][len] = '\0';
                macro->param_count++;
                if (!q) break;
                p = q + 1;
            }
        }
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
    
    // 查找常量 - 改进版本
    macro->constant_count = 0;
    
    // 首先查找预定义的常量
    for (int i = 0; common_constants[i].value != 0; i++) {
        char value_str[16];
        snprintf(value_str, sizeof(value_str), "%u", common_constants[i].value);
        if (strstr(macro->definition, value_str)) {
            macro->constants[macro->constant_count] = kmalloc(strlen(common_constants[i].name) + 1, GFP_KERNEL);
            if (macro->constants[macro->constant_count]) {
                strcpy(macro->constants[macro->constant_count], common_constants[i].name);
                macro->constant_count++;
            }
        }
    }
    
    // 查找十六进制常量
    char *hex_pos = macro->definition;
    while ((hex_pos = strstr(hex_pos, "0x")) != NULL) {
        char *end = hex_pos + 2;
        while ((*end >= '0' && *end <= '9') || (*end >= 'a' && *end <= 'f') || (*end >= 'A' && *end <= 'F')) {
            end++;
        }
        int len = end - hex_pos;
        if (len > 2) {  // 至少有一个十六进制数字
            macro->constants[macro->constant_count] = kmalloc(len + 1, GFP_KERNEL);
            if (macro->constants[macro->constant_count]) {
                strncpy(macro->constants[macro->constant_count], hex_pos, len);
                macro->constants[macro->constant_count][len] = '\0';
                macro->constant_count++;
            }
        }
        hex_pos = end;
    }
    
    // 查找十进制数字常量
    char *def_copy3 = kmalloc(strlen(macro->definition) + 1, GFP_KERNEL);
    if (def_copy3) {
        strcpy(def_copy3, macro->definition);
        char *num_pos = def_copy3;
        
        while (*num_pos) {
            if (*num_pos >= '0' && *num_pos <= '9') {
                char *num_start = num_pos;
                while (*num_pos >= '0' && *num_pos <= '9') {
                    num_pos++;
                }
                int len = num_pos - num_start;
                if (len > 0) {
                    // 检查是否已经存在这个常量
                    bool exists = false;
                    for (int i = 0; i < macro->constant_count; i++) {
                        if (strcmp(macro->constants[i], num_start) == 0) {
                            exists = true;
                            break;
                        }
                    }
                    
                    if (!exists) {
                        macro->constants[macro->constant_count] = kmalloc(len + 1, GFP_KERNEL);
                        if (macro->constants[macro->constant_count]) {
                            strncpy(macro->constants[macro->constant_count], num_start, len);
                            macro->constants[macro->constant_count][len] = '\0';
                            macro->constant_count++;
                        }
                    }
                }
            } else {
                num_pos++;
            }
        }
        kfree(def_copy3);
    }
    
    // 查找操作 - 改进版本，按优先级顺序查找
    macro->op_count = 0;
    const char *ops[] = {
        "<<", ">>",  // 移位操作
        "&&", "||",  // 逻辑操作
        "<=", ">=", "==", "!=",  // 比较操作
        "<", ">",    // 比较操作
        "*", "/", "%",  // 算术操作
        "+", "-",    // 算术操作
        "&", "|", "^",  // 位操作
        "="          // 赋值操作
    };
    
    char *def_copy2 = kmalloc(strlen(macro->definition) + 1, GFP_KERNEL);
    if (def_copy2) {
        strcpy(def_copy2, macro->definition);
        
        for (int i = 0; i < sizeof(ops)/sizeof(ops[0]); i++) {
            char *pos = def_copy2;
            while ((pos = strstr(pos, ops[i])) != NULL) {
                // 检查是否是更长的操作符的一部分
                bool is_part = false;
                for (int j = 0; j < i; j++) {
                    if (strstr(ops[j], ops[i]) && strstr(pos, ops[j])) {
                        is_part = true;
                        break;
                    }
                }
                
                if (!is_part) {
                    macro->operations[macro->op_count] = kmalloc(strlen(ops[i]) + 1, GFP_KERNEL);
                    if (macro->operations[macro->op_count]) {
                        strcpy(macro->operations[macro->op_count], ops[i]);
                        macro->op_count++;
                    }
                }
                pos += strlen(ops[i]);
            }
        }
        kfree(def_copy2);
    }
    
    kfree(def_copy);
    return 0;
}

// 函数：查找指令模式
static int find_instruction_patterns(unsigned char *code, int code_size, 
                                   struct analysis_result *result) {
    int found_count = 0;
    int max_instructions = 50;
    
    result->found_instructions = kmalloc(max_instructions * sizeof(struct assembly_instruction), GFP_KERNEL);
    result->instruction_offsets = kmalloc(max_instructions * sizeof(unsigned long), GFP_KERNEL);
    
    if (!result->found_instructions || !result->instruction_offsets) {
        return -ENOMEM;
    }
    
    for (int i = 0; i < code_size - 16; i++) {
        for (int p = 0; instruction_patterns[p].name != NULL; p++) {
            int match = 1;
            for (int j = 0; j < instruction_patterns[p].pattern_len; j++) {
                if (code[i + j] != instruction_patterns[p].pattern[j]) {
                    match = 0;
                    break;
                }
            }
            
            if (match && found_count < max_instructions) {
                result->found_instructions[found_count] = instruction_patterns[p];
                result->instruction_offsets[found_count] = config.function_addr + i;
                found_count++;
            }
        }
    }
    
    result->instruction_count = found_count;
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

// 函数：生成汇编展开
static char* generate_assembly_expansion(struct macro_definition *macro, 
                                       struct analysis_result *result) {
    char *expansion = kmalloc(4096, GFP_KERNEL);
    if (!expansion) return NULL;
    
    expansion[0] = '\0';
    
    // 生成通用的汇编展开模板
    strcat(expansion, "# 通用宏汇编展开分析\n");
    strcat(expansion, "# 宏名: ");
    strcat(expansion, macro->name);
    strcat(expansion, "\n");
    strcat(expansion, "# 宏定义: ");
    strcat(expansion, macro->definition);
    strcat(expansion, "\n\n");
    
    // 分析参数
    if (macro->param_count > 0) {
        strcat(expansion, "# 参数处理:\n");
        for (int i = 0; i < macro->param_count && i < 6; i++) {
            char param_info[256];
            snprintf(param_info, sizeof(param_info), 
                    "# 参数 %d (%s): 在寄存器 r%d 中\n", 
                    i+1, macro->parameters[i], i+2);
            strcat(expansion, param_info);
        }
        strcat(expansion, "\n");
    }
    
    // 分析常量
    if (macro->constant_count > 0) {
        strcat(expansion, "# 常量处理:\n");
        for (int i = 0; i < macro->constant_count; i++) {
            char const_info[256];
            snprintf(const_info, sizeof(const_info), 
                    "# 常量 %d: %s\n", i+1, macro->constants[i]);
            strcat(expansion, const_info);
        }
        strcat(expansion, "\n");
    }
    
    // 根据操作类型生成汇编代码
    strcat(expansion, "# 操作序列:\n");
    
    for (int i = 0; i < macro->op_count; i++) {
        char *op = macro->operations[i];
        char *op_asm = kmalloc(512, GFP_KERNEL);
        
        if (!op_asm) {
            continue;  // 跳过这个操作，继续处理下一个
        }
        
        if (strcmp(op, "*") == 0) {
            snprintf(op_asm, 512, 
                    "# 乘法操作\n"
                    "imul %%eax,%%r8d            # 执行乘法运算\n");
        } else if (strcmp(op, "+") == 0) {
            snprintf(op_asm, 512, 
                    "# 加法操作\n"
                    "add %%eax,%%r8d             # 执行加法运算\n");
        } else if (strcmp(op, "-") == 0) {
            snprintf(op_asm, 512, 
                    "# 减法操作\n"
                    "sub %%eax,%%r8d             # 执行减法运算\n");
        } else if (strcmp(op, "/") == 0) {
            snprintf(op_asm, 512, 
                    "# 除法操作\n"
                    "div %%eax                   # 执行除法运算\n");
        } else if (strcmp(op, "<") == 0) {
            snprintf(op_asm, 512, 
                    "# 小于比较\n"
                    "cmp %%rax,%%rcx             # 比较两个值\n"
                    "jl macro_true              # 如果小于则跳转\n");
        } else if (strcmp(op, ">") == 0) {
            snprintf(op_asm, 512, 
                    "# 大于比较\n"
                    "cmp %%rax,%%rcx             # 比较两个值\n"
                    "jg macro_true              # 如果大于则跳转\n");
        } else if (strcmp(op, "<=") == 0) {
            snprintf(op_asm, 512, 
                    "# 小于等于比较\n"
                    "cmp %%rax,%%rcx             # 比较两个值\n"
                    "jle macro_true             # 如果小于等于则跳转\n");
        } else if (strcmp(op, ">=") == 0) {
            snprintf(op_asm, 512, 
                    "# 大于等于比较\n"
                    "cmp %%rax,%%rcx             # 比较两个值\n"
                    "jge macro_true             # 如果大于等于则跳转\n");
        } else if (strcmp(op, "==") == 0) {
            snprintf(op_asm, 512, 
                    "# 相等比较\n"
                    "cmp %%rax,%%rcx             # 比较两个值\n"
                    "je macro_true              # 如果相等则跳转\n");
        } else if (strcmp(op, "!=") == 0) {
            snprintf(op_asm, 512, 
                    "# 不等比较\n"
                    "cmp %%rax,%%rcx             # 比较两个值\n"
                    "jne macro_true             # 如果不相等则跳转\n");
        } else if (strcmp(op, "&") == 0) {
            snprintf(op_asm, 512, 
                    "# 位与操作\n"
                    "and %%eax,%%r8d             # 执行位与运算\n");
        } else if (strcmp(op, "|") == 0) {
            snprintf(op_asm, 512, 
                    "# 位或操作\n"
                    "or %%eax,%%r8d              # 执行位或运算\n");
        } else if (strcmp(op, "^") == 0) {
            snprintf(op_asm, 512, 
                    "# 位异或操作\n"
                    "xor %%eax,%%r8d             # 执行位异或运算\n");
        } else if (strcmp(op, "<<") == 0) {
            snprintf(op_asm, 512, 
                    "# 左移操作\n"
                    "shl %%cl,%%r8d              # 执行左移运算\n");
        } else if (strcmp(op, ">>") == 0) {
            snprintf(op_asm, 512, 
                    "# 右移操作\n"
                    "shr %%cl,%%r8d              # 执行右移运算\n");
        } else {
            snprintf(op_asm, 512, 
                    "# 未知操作: %s\n"
                    "# 需要手动分析此操作的汇编实现\n", op);
        }
        
        strcat(expansion, op_asm);
        strcat(expansion, "\n");
        kfree(op_asm);
    }
    
    // 添加优化建议
    strcat(expansion, "# 编译器优化分析:\n");
    
    // 检查是否有乘法优化
    bool has_multiplication = false;
    for (int i = 0; i < macro->op_count; i++) {
        if (strcmp(macro->operations[i], "*") == 0) {
            has_multiplication = true;
            break;
        }
    }
    
    if (has_multiplication) {
        strcat(expansion, "# 乘法优化建议:\n");
        strcat(expansion, "# - 常数乘法可能被优化为移位和加法\n");
        strcat(expansion, "# - 例如: x * 1280 = x * (1024 + 256) = x * 1024 + x * 256\n");
        strcat(expansion, "# - 或者: x * 1280 = x * 5 * 256 = (x * 5) << 8\n");
        strcat(expansion, "# - 编译器可能使用 lea 指令进行快速乘法\n\n");
    }
    
    // 检查是否有比较操作
    bool has_comparison = false;
    for (int i = 0; i < macro->op_count; i++) {
        if (strstr(macro->operations[i], "<") || strstr(macro->operations[i], ">") ||
            strstr(macro->operations[i], "==") || strstr(macro->operations[i], "!=")) {
            has_comparison = true;
            break;
        }
    }
    
    if (has_comparison) {
        strcat(expansion, "# 比较操作优化:\n");
        strcat(expansion, "# - 编译器可能重新排列比较顺序\n");
        strcat(expansion, "# - 可能使用条件移动指令 (cmov) 而不是跳转\n");
        strcat(expansion, "# - 可能合并多个比较操作\n\n");
    }
    
    // 添加性能分析
    strcat(expansion, "# 性能分析:\n");
    if (result->total_clock_cycles > 0) {
        char perf_info[256];
        snprintf(perf_info, sizeof(perf_info), 
                "# 总执行时间: %d 个时钟周期\n", result->total_clock_cycles);
        strcat(expansion, perf_info);
    }
    
    strcat(expansion, "# 指令级并行性: 现代CPU可以同时执行多个指令\n");
    strcat(expansion, "# 缓存友好性: 数据局部性对性能影响很大\n");
    strcat(expansion, "# 分支预测: 条件跳转可能影响流水线效率\n\n");
    
    // 添加调试信息
    strcat(expansion, "# 调试建议:\n");
    strcat(expansion, "# 1. 使用 objdump -d 查看实际汇编代码\n");
    strcat(expansion, "# 2. 使用 perf record/report 分析性能热点\n");
    strcat(expansion, "# 3. 使用 gdb 单步调试汇编代码\n");
    strcat(expansion, "# 4. 检查编译器优化选项的影响\n");
    
    return expansion;
}

// 函数：分析宏展开
static void analyze_macro_expansion(void) {
    printk(KERN_INFO "=== 高级通用宏汇编分析工具 ===\n");
    printk(KERN_INFO "函数名: %s\n", config.function_name);
    printk(KERN_INFO "函数地址: 0x%lx\n", config.function_addr);
    printk(KERN_INFO "宏名: %s\n", config.macro.name);
    printk(KERN_INFO "宏定义: %s\n", config.macro.definition);
    
    printk(KERN_INFO "宏参数: ");
    for (int i = 0; i < config.macro.param_count; i++) {
        printk(KERN_INFO "%s ", config.macro.parameters[i]);
    }
    printk(KERN_INFO "\n");
    
    printk(KERN_INFO "宏中使用的常量: ");
    for (int i = 0; i < config.macro.constant_count; i++) {
        printk(KERN_INFO "%s ", config.macro.constants[i]);
    }
    printk(KERN_INFO "\n");
    
    printk(KERN_INFO "宏中的操作: ");
    for (int i = 0; i < config.macro.op_count; i++) {
        printk(KERN_INFO "%s ", config.macro.operations[i]);
    }
    printk(KERN_INFO "\n\n");
    
    // 查找指令模式
    printk(KERN_INFO "=== 查找指令模式 ===\n");
    int found_patterns = find_instruction_patterns(config.function_code, config.code_size, 
                                                  &config.result);
    printk(KERN_INFO "找到 %d 个指令模式:\n", found_patterns);
    
    for (int i = 0; i < config.result.instruction_count; i++) {
        printk(KERN_INFO "  %d. %s 在偏移 0x%lx: ", 
               i+1, config.result.found_instructions[i].name, 
               config.result.instruction_offsets[i]);
        
        // 打印机器码
        for (int k = 0; k < config.result.found_instructions[i].pattern_len; k++) {
            printk(KERN_INFO "%02x ", config.result.found_instructions[i].pattern[k]);
        }
        printk(KERN_INFO "- %s (%d 时钟周期)\n", 
               config.result.found_instructions[i].description,
               config.result.found_instructions[i].clock_cycles);
    }
    printk(KERN_INFO "\n");
    
    // 查找常量
    printk(KERN_INFO "=== 查找常量 ===\n");
    int found_constants = find_constants(config.function_code, config.code_size);
    printk(KERN_INFO "找到 %d 个常量\n\n", found_constants);
    
    // 生成汇编展开
    printk(KERN_INFO "=== 宏汇编展开 ===\n");
    config.result.assembly_expansion = generate_assembly_expansion(&config.macro, &config.result);
    if (config.result.assembly_expansion) {
        printk(KERN_INFO "%s\n", config.result.assembly_expansion);
    }
    
    // 计算总时钟周期
    config.result.total_clock_cycles = 0;
    for (int i = 0; i < config.result.instruction_count; i++) {
        config.result.total_clock_cycles += config.result.found_instructions[i].clock_cycles;
    }
    printk(KERN_INFO "总执行时间: %d 个时钟周期\n\n", config.result.total_clock_cycles);
    
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

// 函数：执行分析
static int perform_analysis(const char *function_name, const char *macro_def) {
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

// 函数：清理资源
static void cleanup_analysis_result(struct analysis_result *result) {
    if (result->found_instructions) {
        kfree(result->found_instructions);
    }
    if (result->instruction_offsets) {
        kfree(result->instruction_offsets);
    }
    if (result->assembly_expansion) {
        kfree(result->assembly_expansion);
    }
}

static int __init advanced_macro_analyzer_init(void) {
    printk(KERN_INFO "=== 高级通用宏汇编分析工具启动 ===\n");
    
    // 组合宏定义的两个部分
    char combined_macro_def[512];
    snprintf(combined_macro_def, sizeof(combined_macro_def), "%s %s", 
             macro_def_part1, macro_def_part2);
    
    printk(KERN_INFO "分析函数: %s\n", user_function_name);
    printk(KERN_INFO "分析宏: %s\n", combined_macro_def);
    
    if (parse_macro_definition(combined_macro_def, &config.macro) < 0) {
        printk(KERN_ERR "Failed to parse macro definition\n");
        return -1;
    }
    strcpy(config.function_name, user_function_name);
    
    int ret = perform_analysis(user_function_name, combined_macro_def);
    
    if (ret == 0) {
        printk(KERN_INFO "分析完成\n");
    } else {
        printk(KERN_ERR "分析失败: %d\n", ret);
    }
    
    // 清理资源
    cleanup_analysis_result(&config.result);
    
    return 0;
}

static void __exit advanced_macro_analyzer_exit(void) {
    printk(KERN_INFO "高级通用宏汇编分析工具卸载\n");
}

module_init(advanced_macro_analyzer_init);
module_exit(advanced_macro_analyzer_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Advanced generic macro assembly analyzer"); 