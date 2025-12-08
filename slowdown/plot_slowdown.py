import os
import re
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter, FixedLocator
import matplotlib.cm as cm
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

def apply_paper_style(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)
    ax.tick_params(axis='both', which='major', length=10, width=2)
    ax.grid(True, alpha=0.3, zorder=0, linestyle='--')

def iops_formatter(x, pos):
    """将X轴 IOPS 格式化为百万单位 (M)"""
    # 如果 x 小于 1M，显示一位小数，例如 0.1M
    if x < 1_000_000 and x > 0:
        return f'{x/1_000_000:.1f}'
    return f'{int(x/1_000_000)}'

def percent_formatter(x, pos):
    """将Y轴数值（小数）格式化为百分比字符串，但隐藏 0%"""
    if x == 0:
        return ''  # 或者 return ' ' 如果你希望保留一点空隙
    return f'{int(x * 100)}%'

# --- 2. 数据读取与处理 (Data Parsing & Calculation) ---
# [用户指定] 从 100,000 开始
start_iops = 100_000 
end_iops = 10_000_000 
step = 100_000      # 步长调整为 100k 以匹配起点

data_dir = os.path.dirname(os.path.abspath(__file__))
data_dir += "/data"

# [自动化] 扫描目录下所有的 delay 值
detected_delays = set()
# 匹配文件名格式: base_2_100000.txt 或 xk_5_200000.txt
filename_pattern = re.compile(r'(?:base|xk)_(\d+)_(\d+)\.txt')

print(f"正在扫描数据目录: {data_dir}")
if os.path.exists(data_dir):
    for f in os.listdir(data_dir):
        match = filename_pattern.match(f)
        if match:
            # group(1) 是 delay, group(2) 是 iops
            detected_delays.add(int(match.group(1)))

sorted_delays = sorted(list(detected_delays))
print(f"自动检测到的 Delays: {sorted_delays} us")

if not sorted_delays:
    print("未找到符合格式的数据文件。")
    # 为了防止报错，给一个默认空列表，后续绘图会跳过
    plot_data_map = {}
else:
    # 存储所有 delay 的绘图数据
    # 结构: { delay_val: {'iops': [], 'slowdown_p50': [], 'slowdown_p99': []} }
    plot_data_map = {}

    for delay in sorted_delays:
        print(f"正在处理 Delay = {delay} us 的数据...")
        
        raw_data = {
            'base': {'p50': {}, 'p99': {}}, 
            'xk':   {'p50': {}, 'p99': {}}
        }
        prefixes = ['base', 'xk']
        
        # 读取该 delay 下的所有 iops 数据
        for prefix in prefixes:
            for iops in range(start_iops, end_iops + 1, step):
                filename = os.path.join(data_dir, f"{prefix}_{delay}_{iops}.txt")
                
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        content = f.read()
                    
                    p50_match = re.search(r'P50[:\s]+(\d+)', content, re.IGNORECASE)
                    if p50_match:
                        raw_data[prefix]['p50'][iops] = int(p50_match.group(1))
                        
                    p99_match = re.search(r'P99[:\s]+(\d+)', content, re.IGNORECASE)
                    if p99_match:
                        raw_data[prefix]['p99'][iops] = int(p99_match.group(1))

        # 计算该 delay 的 Slowdown
        current_plot_data = {
            'iops': [],
            'slowdown_p50': [],
            'slowdown_p99': []
        }
        
        common_iops = sorted(list(set(raw_data['base']['p50'].keys()) & set(raw_data['xk']['p50'].keys())))
        
        for iops in common_iops:
            if iops in raw_data['base']['p99'] and iops in raw_data['xk']['p99']:
                base_p50 = raw_data['base']['p50'][iops]
                xk_p50 = raw_data['xk']['p50'][iops]
                base_p99 = raw_data['base']['p99'][iops]
                xk_p99 = raw_data['xk']['p99'][iops]
                
                if base_p50 > 0 and base_p99 > 0:
                    current_plot_data['iops'].append(iops)
                    current_plot_data['slowdown_p50'].append((xk_p50 - base_p50) / base_p50)
                    current_plot_data['slowdown_p99'].append((xk_p99 - base_p99) / base_p99)
        
        if current_plot_data['iops']:
            plot_data_map[delay] = current_plot_data
            sd = (current_plot_data['slowdown_p50'][-1] * 100)
            print(f"Slowdown for {delay}us {iops/1_000_000}M: {sd:.0f}%")

# --- 3. 绘图 (Plotting) ---
if plot_data_map:
    fig, ax = plt.subplots(figsize=(8, 4)) # 稍微加宽一点以容纳图例

    line_width = 2
    marker_size = 7.5
    
    # 遍历每个 delay 进行绘图
    for idx, delay in enumerate(sorted_delays):
        if delay not in plot_data_map:
            continue
            
        data = plot_data_map[delay]
        color = plot_common.colors[idx % len(plot_common.colors)]
        marker = plot_common.markers[idx % len(plot_common.markers)]
        
        # 绘制 P50 (虚线)
        ax.plot(data['iops'], data['slowdown_p50'], 
                color=color, linestyle='--', linewidth=line_width,
                marker=marker, markersize=marker_size, markevery=1,
                label=f'{delay}us P50')

    # --- 4. 样式调整 (Styling) ---
    apply_paper_style(ax)

    ax.set_xlabel(r'Offered IOPS ($\times10^6$/s)') 
    ax.set_ylabel('Slowdown (%)')

    # Y 轴范围
    ax.set_ylim(0, 0.20)  # 稍微扩大一点范围到 15% 以防重叠
    y_ticks = [0, 0.01, 0.05, 0.10, 0.15, 0.20]
    ax.yaxis.set_major_locator(FixedLocator(y_ticks))
    ax.yaxis.set_major_formatter(FuncFormatter(percent_formatter))

    ax.axhline(y=0, color='black', linestyle=':', linewidth=2, alpha=0.8, zorder=1)

    # X 轴格式化
    ax.xaxis.set_major_formatter(FuncFormatter(iops_formatter))
    
    # 确定 X 轴范围
    all_iops = []
    for d in plot_data_map:
        all_iops.extend(plot_data_map[d]['iops'])
    
    if all_iops:
        min_iops = min(all_iops)
        max_iops = max(all_iops)
        
        # 智能刻度步长
        tick_step = 1_000_000 # 默认 1M
        if (max_iops - min_iops) < 2_000_000:
            tick_step = 200_000 # 如果范围很小，用 200k
        elif (max_iops - min_iops) > 15_000_000:
            tick_step = 2_000_000
            
        # 确保刻度从整百万或整十万开始
        start_tick = (min_iops // tick_step) * tick_step
        major_ticks = np.arange(start_tick, max_iops + tick_step, tick_step)
        # 过滤掉小于 min_iops 太多的刻度
        major_ticks = [t for t in major_ticks if t >= min_iops - (tick_step/2)]
        
        ax.set_xticks(major_ticks)
        ax.set_xlim(min_iops, max_iops)

        # --- 添加 0 到 1_000_000 之间的次要刻度（不显示标签） ---
        if min_iops < 1_000_000:
            # 生成 0 到 1_000_000 的刻度，步长 100_000（可调）
            minor_ticks_0_to_1M = np.arange(0, 1_000_001, 100_000)
            # 只保留在当前 xlim 范围内的
            minor_ticks_0_to_1M = [t for t in minor_ticks_0_to_1M if t >= 0 and t <= max_iops]
            
            # 设置为次要刻度
            ax.set_xticks(minor_ticks_0_to_1M, minor=True)
            
            # 隐藏次要刻度的标签（关键！）
            ax.tick_params(axis='x', which='minor', labelbottom=False)
            
            # （可选）让次要刻度线更短、更细，区别于主刻度
            ax.tick_params(axis='x', which='minor', length=4, width=1, color='gray')

    # 在 X 轴 1M 和 1.9M 处添加箭头和文本 "saturated"
    saturated_positions = [1_000_000, 1_900_000]
    saturated_y_positions = [0.03, 0.05]
    for pos, y_pos in zip(saturated_positions, saturated_y_positions):
        if pos >= min_iops and pos <= max_iops:
            ax.annotate('Saturated', xy=(pos, y_pos), xytext=(pos, y_pos + 0.015),
                        arrowprops=dict(arrowstyle='->', color='black', lw=1.5,
                                       shrinkA=0, shrinkB=0),
                        ha='center', va='bottom', fontsize=20, color='black')

    # 图例设置 (分列显示以节省空间)
    legend = ax.legend(loc='upper left', ncol=3, 
                       frameon=True, facecolor='white', framealpha=1.0, fontsize=20,
                       handlelength=2.0)

    plt.tight_layout()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plot_common.save_fig(script_dir, 'slowdown')
    plt.close()
else:
    print("没有数据可绘图。")