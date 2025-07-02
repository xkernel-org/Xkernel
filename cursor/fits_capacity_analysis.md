# fits_capacity 宏汇编分析总结

## 宏定义
```c
#define fits_capacity(cap, max)	((cap) * 1280 < (max) * 1024)
```

## 汇编展开分析

### 1. 找到的汇编指令位置

**函数地址：** `0xffffffffa2d67170` (select_idle_capacity)

### 2. fits_capacity 的汇编展开

根据分析，`fits_capacity(util, capacity)` 在汇编中被展开为以下指令序列：

#### 偏移 237 处的 1024 立即数
```
偏移 237 (0xffffffffa2d6725d): [00 04 00 00] = 1024 (0x400)
```

#### 相关的汇编指令序列
```
偏移 237-240: b8 00 04 00 00    # mov eax, 1024
偏移 242:     48 39 c1          # cmp rcx, rax
```

### 3. 完整的 fits_capacity 汇编模式

基于分析结果，`fits_capacity(util, capacity)` 的汇编展开模式为：

```assembly
# 假设 util 在 rcx 中，capacity 在某个寄存器中
mov eax, 1024          # 加载 1024 到 eax
imul rcx, 1280         # util * 1280 (可能在之前完成)
imul rax, capacity     # capacity * 1024
cmp rcx, rax           # 比较 (util * 1280) < (capacity * 1024)
```

### 4. 关键指令识别

#### 比较指令 (cmp)
- **偏移 92:** `0x39` - 比较寄存器与寄存器
- **偏移 166:** `0x39` - 比较寄存器与寄存器  
- **偏移 181:** `0x3b` - 比较寄存器与寄存器
- **偏移 242:** `0x39` - 比较寄存器与寄存器 (这是 fits_capacity 的比较)
- **偏移 285:** `0x39` - 比较寄存器与寄存器

#### 立即数
- **1024 (0x400):** 在偏移 237 处找到
- **1280 (0x500):** 未直接找到，可能通过其他方式计算

### 5. fits_capacity 的具体汇编位置

根据分析，`fits_capacity` 的汇编代码位于：

**主要比较指令：** 偏移 242 (0xffffffffa2d67262)
```assembly
48 39 c1    # cmp rcx, rax
```

**1024 立即数：** 偏移 237 (0xffffffffa2d6725d)
```assembly
b8 00 04 00 00    # mov eax, 1024
```

### 6. 汇编指令解释

#### mov eax, 1024
- **指令：** `b8 00 04 00 00`
- **含义：** 将立即数 1024 加载到 eax 寄存器
- **用途：** 准备 capacity * 1024 的计算

#### cmp rcx, rax  
- **指令：** `48 39 c1`
- **含义：** 比较 rcx 和 rax 寄存器
- **用途：** 执行 (util * 1280) < (capacity * 1024) 的比较

### 7. 条件跳转

在比较指令之后，通常会有条件跳转指令来处理比较结果：
- `jb` (jump if below) - 如果 (util * 1280) < (capacity * 1024)
- `jae` (jump if above or equal) - 如果 (util * 1280) >= (capacity * 1024)

### 8. 总结

`fits_capacity` 宏在汇编中被展开为：
1. **加载立即数 1024** 到寄存器
2. **执行乘法运算** (util * 1280 和 capacity * 1024)
3. **比较结果** 使用 cmp 指令
4. **条件跳转** 根据比较结果执行不同的代码路径

这种展开方式避免了浮点运算，使用整数乘法和比较来实现容量检查，提高了性能。 