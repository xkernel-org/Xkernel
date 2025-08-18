import pandas as pd
import glob
import os

# --- 配置 ---
input_file_pattern = 'filtered_*_numeric.csv'
output_dir = 'potential_res' 

os.makedirs(output_dir, exist_ok=True)

print(f"脚本将在当前目录下运行，查找文件模式: '{input_file_pattern}'")
print(f"结果将保存到目录: '{output_dir}'")


# --- 筛选逻辑：四大规则 ---

# 规则A: 基于名称的关键字
perf_keywords = [
    'SIZE', 'MAX', 'NR_', 'COUNT', 'BUFFER', 'TIMEOUT', 'DELAY', 'CACHE',
    'ORDER', 'THRESHOLD', 'LIMIT', 'BATCH', 'WATERMARK', 'RETRIES', 'QUEUE',
    'SHIFT', 'SCALE', 'FACTOR', 'RATIO', 'PERIOD', 'SLOTS', 'NUMA', 
    'INTERVAL', 'DEPTH'
]
keyword_regex = '(?i)' + '|'.join(perf_keywords)

# 规则B: 基于值的“魔术数字”表达式
value_regex = r'.*[0-9].*[\*\/\+\-\<\>\&\|\^]|.*[\*\/\+\-\<\>\&\|\^].*[0-9]'

# 规则C: 基于结构的函数式宏
function_macro_regex = r'\w+\(.*?\)'

# ==================================================================
# VVVV 这里是新增的关键逻辑 VVVV
# 规则D: 值是单纯的、非平庸的数字
# 定义一个我们想要忽略的“平庸”数字列表
# ignore_numbers = {0, 1, 2, -1}
ignore_numbers = {0, 1, -1}
# ^^^^ 这里是新增的关键逻辑 ^^^^
# ==================================================================


# --- 主处理逻辑 ---
input_files = glob.glob(input_file_pattern)

if not input_files:
    print("\n错误：在当前目录下没有找到任何匹配的文件。")
else:
    print(f"\n找到了 {len(input_files)} 个文件进行处理:")
    for f in input_files:
        print(f" - {f}")

for filepath in input_files:
    print(f"\n--- 处理文件: {filepath} ---")
    try:
        df = pd.read_csv(filepath)
        # 预处理'Value'列，尝试将其转换为数字，非数字的会变成NaN
        df['Value_numeric'] = pd.to_numeric(df['Value'], errors='coerce')

        # 应用四大筛选条件
        condition_A = df['Name'].str.contains(keyword_regex, na=False)
        condition_B = df['Value'].astype(str).str.match(value_regex, na=False)
        condition_C = df['Name'].str.contains(function_macro_regex, na=False)
        
        # 应用规则D
        # 1. 必须是数字 (非NaN)
        # 2. 不能在我们的忽略列表中
        is_simple_number = df['Value_numeric'].notna()
        is_not_ignored = ~df['Value_numeric'].isin(ignore_numbers)
        condition_D = is_simple_number & is_not_ignored

        # 组合所有条件 (满足任一即可)
        combined_condition = condition_A | condition_B | condition_C | condition_D
        
        # 去掉我们为计算而添加的临时列
        df_potential = df[combined_condition].drop(columns=['Value_numeric'])

        if df_potential.empty:
            print(" -> 未在该文件中找到潜在的性能相关宏。")
            continue

        base_name = os.path.basename(filepath)
        output_filename = base_name.replace('filtered_', 'potential_perf_').replace('_numeric', '')
        output_path = os.path.join(output_dir, output_filename)

        df_potential.to_csv(output_path, index=False)
        print(f" -> 发现 {len(df_potential)} 个潜在宏，结果已保存到: {output_path}")

    except Exception as e:
        print(f"处理文件 {filepath} 时发生错误: {e}")

print("\n--- 所有文件处理完毕 ---")