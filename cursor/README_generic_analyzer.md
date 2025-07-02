# 通用宏汇编分析工具

## 概述

这是一个通用的宏汇编分析工具，能够自动分析任意函数中的任意宏展开，并输出完整的汇编指令序列。

## 功能特点

### 1. 通用性
- 支持任意函数名作为输入
- 支持任意宏定义作为输入
- 自动解析宏参数、常量和操作

### 2. 智能分析
- 自动识别常见的汇编指令模式
- 自动检测宏中使用的常量
- 智能生成可能的汇编展开

### 3. 详细输出
- 完整的指令序列（不省略任何指令）
- 每条指令的机器码和说明
- 执行时间分析
- 编译器优化分析

## 工具版本

### 1. 基础版本 (`generic_macro_analyzer.c`)
- 基本的宏解析功能
- 预定义的指令模式匹配
- 常量检测

### 2. 高级版本 (`advanced_macro_analyzer.c`)
- 完整的宏解析（参数、常量、操作）
- 更多的指令模式
- 智能汇编展开生成
- 性能分析

## 使用方法

### 1. 编译模块
```bash
make
```

### 2. 加载模块
```bash
# 基础版本
sudo insmod generic_macro_analyzer.ko

# 高级版本
sudo insmod advanced_macro_analyzer.ko
```

### 3. 查看结果
```bash
sudo dmesg | tail -100
```

### 4. 卸载模块
```bash
sudo rmmod generic_macro_analyzer
sudo rmmod advanced_macro_analyzer
```

## 输入格式

### 函数名
- 必须是内核中存在的函数符号
- 例如：`select_idle_capacity`

### 宏定义
- 标准C宏定义格式
- 例如：`fits_capacity(cap, max) ((cap) * 1280 < (max) * 1024)`

## 输出内容

### 1. 宏解析结果
```
宏名: fits_capacity
宏定义: ((cap) * 1280 < (max) * 1024)
宏参数: cap max
宏中使用的常量: 1280 1024
宏中的操作: * <
```

### 2. 指令模式匹配
```
找到指令模式 'LEA_MUL_5' 在偏移 193 (0xffffffffa2d67231): 
48 8d 04 89 - LEA instruction for multiplication by 5

找到指令模式 'SHL_256' 在偏移 217 (0xffffffffa2d67249): 
48 c1 e0 08 - Shift left by 8 (multiply by 256)
```

### 3. 常量检测
```
找到常量 1024 (1024) 在偏移 236 (0xffffffffa2d6725c): 
b8 00 04 00 00 - Capacity scaling factor
```

### 4. 汇编展开
```
# fits_capacity 类型的宏展开
# 1. 计算第一个参数 * 1280 (优化版本):
lea (%rcx,%rcx,4),%rax    # rax = rcx * 5
shl $0x8,%rax             # rax = rax * 256 (总共乘以 1280)

# 2. 计算第二个参数 * 1024:
mov $0x400,%eax           # eax = 1024
imul %eax,%r8d            # r8d = capacity * 1024

# 3. 比较操作:
cmp %rax,%r8d             # 比较两个结果

# 4. 条件跳转:
jl macro_true              # 根据比较结果跳转
```

## 自定义分析

要分析其他函数和宏，可以修改代码中的以下部分：

### 1. 基础版本
```c
// 在 generic_macro_analyzer_init 函数中修改
const char *function_name = "your_function_name";
const char *macro_def = "your_macro_name(param1, param2) your_macro_definition";
```

### 2. 高级版本
```c
// 在 advanced_macro_analyzer_init 函数中修改
const char *function_name = "your_function_name";
const char *macro_def = "your_macro_name(param1, param2) your_macro_definition";
```

## 注意事项

1. 需要内核调试符号支持
2. 函数必须在 `/proc/kallsyms` 中可见
3. 宏必须是内联展开的（不是函数调用）
4. 分析结果基于实际运行的代码，可能因编译器优化而有所不同

这个工具提供了完整的宏汇编分析功能，可以帮助理解编译器如何优化宏展开，以及生成的汇编代码的性能特征。 