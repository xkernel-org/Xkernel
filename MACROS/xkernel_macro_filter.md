# xkernel_macro_filter

## Problems

原筛选脚本中的问题, 包括但不限于:

1. 正则表达式的识别规则无法识别 `symbol.csv` 中的一些例子, 例如 `fits_capacity`. 

2. 对 `subsystem` 的识别分类不够完全且有一定错误. 例如需新增对于 `block`, `io_uring` 等的识别. 以及出现了以下的识别情况:
```csv
mm,/home/spike/linux-6.14/tools/mm/slabinfo.c,24,macro,MAX_SLABS,2000,
```
理论上对于 `tools` 下的任意 `subsystem` 不应被识别到其中.

3. 无法识别 `enum` 以及内联函数返回常量.

## Solutions

1. 修改正则表达式规则以识别名称为小写的宏:

```py
define_pattern = re.compile(r'^\s*#define\s+([a-zA-Z0-9_]+(?:\(.*\))?)(?:\s+(.+))?$')
static_const_pattern = re.compile(r'^\s*static\s+const\s+[\w\s\*]+\s+([a-zA-Z0-9_]+)\s*=\s*(.+);')
```

2. 新增 `block`, `io_uring`. 以及修改 `extract.py` 的筛选规则, 当前只关注 `~/linux-6.14/subsystem` 下的文件, 忽略例如 `~/linux-6.14/tools/` 等文件. 

3. TBD

## Target filter rules
