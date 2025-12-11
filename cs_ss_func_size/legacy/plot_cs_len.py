import matplotlib.pyplot as plt
import os
from collections import Counter

# --- 1. 设置全局绘图风格 ---
plt.rcParams['font.family'] = 'helvetica'
plt.rcParams['font.size'] = 34

def parse_data(file_path):
    """
    读取文件并解析数据 (不使用 pandas)
    """
    data = []
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return []

    with open(file_path, 'r') as f:
        content = f.read()
    
    # 统一处理换行和逗号分隔
    tokens = content.replace('\n', ',').split(',')
    
    for token in tokens:
        token = token.strip()
        if token:
            try:
                val = float(token)
                if val.is_integer():
                    val = int(val)
                data.append(val)
            except ValueError:
                continue
    return data

# --- 2. 读取与处理数据 ---
file_path = 'cs_instr_len.txt'
data = parse_data(file_path)

if data:
    # 统计频次
    counter = Counter(data)
    
    # --- 关键修改：强制加入数字 6 ---
    # 即使数据里没有6，我们手动把它的频次设为0，或者确保它出现在键列表中
    # 使用 set 确保不重复，并加入 6
    all_keys = set(counter.keys())
    all_keys.add(6) 
    
    sorted_x = sorted(list(all_keys))
    # 获取对应的频次，如果不存在则为 0
    sorted_y = [counter[x] for x in sorted_x]

    # --- 3. 绘图 ---
    fig, ax = plt.subplots(figsize=(10, 6))

    # 绘制柱状图
    bars = ax.bar(sorted_x, sorted_y, color='gray', width=0.6, zorder=2)

    # 添加柱子顶部的数字标签
    for bar in bars:
        height = bar.get_height()
        # 对于高度为0的柱子（比如6），也显示 "0"
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=34)

    # 强制显示所有横坐标刻度 (包括 6)
    ax.set_xticks(sorted_x)
    ax.set_xticklabels([str(x) for x in sorted_x])
    ax.tick_params(axis='x', length=0)

    # 指定纵坐标刻度
    ax.set_yticks([0, 50, 100, 150])
    ax.set_ylim(0, 180) 

    # 坐标轴标签
    ax.set_xlabel('# of instructions', fontsize=34)
    ax.set_ylabel('Count', fontsize=34)

    # 刻度风格
    ax.tick_params(axis='x', labelsize=34, length=8, width=2)
    ax.tick_params(axis='y', labelsize=34, length=8, width=2)

    # 网格

    # 边框风格
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(2.5)
    ax.spines['bottom'].set_linewidth(2.5)

    # 调整布局
    plt.tight_layout()

    # 保存
    plt.savefig('cs_instr_len_bar.pdf', dpi=300, bbox_inches='tight')
    plt.show()

else:
    print("没有读取到有效数据。")