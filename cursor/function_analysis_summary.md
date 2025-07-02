# 内核函数地址查找分析总结

## 问题描述
在 `/proc/kallsyms` 中可以找到 `select_idle_capacity` 的起始函数地址和结尾函数地址，但在 `select_idle_capacity` 中调用的 `util_fits_cpu` 如何找到他的起始地址？这里的主要问题是 `util_fits_cpu` 是一个 inline 函数。

## 解决方案

### 1. 找到 select_idle_capacity 函数的地址

**方法1：使用 /proc/kallsyms**
```bash
sudo cat /proc/kallsyms | grep "select_idle_capacity"
```
结果：
```
ffffffffa2d67160 t __pfx_select_idle_capacity
ffffffffa2d67170 t select_idle_capacity
```

**方法2：使用内核模块和 kprobe**
```c
static struct kprobe kp = {
    .symbol_name = "select_idle_capacity",
};
ret = register_kprobe(&kp);
if (ret == 0) {
    printk("select_idle_capacity found at address: 0x%lx\n", (unsigned long)kp.addr);
    unregister_kprobe(&kp);
}
```

### 2. 分析 select_idle_capacity 函数中的函数调用

通过分析编译后的机器码，我们找到了以下函数调用：

| 偏移量 | 调用地址 | 函数名 | 说明 |
|--------|----------|--------|------|
| 0 | 0xffffffffc14c5000 | 未知 | 可能是模块地址 |
| 63 | 0xffffffffa345c5d0 | __bitmap_and | 位图操作函数 |
| 104 | 0xffffffffa2d59a90 | uclamp_eff_value | 获取 uclamp 有效值 |
| 121 | 0xffffffffa2d59a90 | uclamp_eff_value | 获取 uclamp 有效值 |
| 156 | 0xffffffffa3465910 | _find_next_bit | 查找下一个位 |

### 3. util_fits_cpu 函数的情况

**重要发现：**
- `util_fits_cpu` 是一个 `static inline` 函数
- 在 `/proc/kallsyms` 中找不到 `util_fits_cpu` 的符号
- 使用 kprobe 也无法找到 `util_fits_cpu` 的独立地址

**原因：**
`static inline` 函数在编译时会被内联展开到调用它的函数中，不会生成独立的函数符号。

### 4. 如何找到 util_fits_cpu 的代码位置

**方法1：通过源代码分析**
根据源代码，`util_fits_cpu` 在 `select_idle_capacity` 中的调用位置：
```c
fits = util_fits_cpu(task_util, util_min, util_max, cpu);
```

**方法2：通过反汇编分析**
1. 获取 `select_idle_capacity` 函数的机器码
2. 分析代码模式，找到 `util_fits_cpu` 内联展开的代码
3. 通过调试器或反汇编工具分析具体的代码位置

**方法3：使用 ftrace**
```bash
# 启用函数跟踪
echo function > /sys/kernel/debug/tracing/current_tracer
echo select_idle_capacity > /sys/kernel/debug/tracing/set_ftrace_filter
```

### 5. 实际地址信息

- **select_idle_capacity 函数地址：** `0xffffffffa2d67170`
- **函数大小：** 约 200-300 字节（根据分析）
- **util_fits_cpu：** 内联展开，无独立地址

### 6. 总结

对于 inline 函数 `util_fits_cpu`：
1. 它没有独立的函数地址
2. 它的代码被内联展开到调用它的函数中
3. 要找到它的代码，需要分析调用函数的机器码
4. 可以通过反汇编工具或调试器来定位具体的代码位置

这种方法适用于所有 `static inline` 函数的情况。 