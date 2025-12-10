import glob
import re
import os
import matplotlib.pyplot as plt
import numpy as np
import sys
import seaborn as sns
from matplotlib.ticker import LogLocator

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import plot_common

# Unified color palette
palette = sns.color_palette("mako")

# Text sizes
TEXT_SIZE_XYLABEL = 18
TEXT_SIZE_XYAXIS = 18
TEXT_SIZE_LEGEND = 16

# Tick parameters
TICK_LENGTH_X = 5
TICK_WIDTH_X = 1 

def apply_academic_style(ax):
    """应用学术图表风格 + Log设置"""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)
    
    # 设置 Y 轴为对数坐标
    ax.set_yscale('log')
    
    # [修改点1] 仅显示主刻度(major)的网格线，解决"虚线过多"的问题
    # 之前是 'both'，现在改为 'major'
    
    ax.tick_params(width=2.5, length=6, which='major', labelsize=TEXT_SIZE_XYAXIS)
    ax.tick_params(width=1.5, length=4, which='minor')

def parse_and_plot_styled():
    # --- 2. 数据解析 ---
    files = glob.glob('L*-*.txt')
    data_map = {}
    all_l_values = set()
    all_threads = set()

    print(f"找到 {len(files)} 个文件。正在处理...")

    for filepath in files:
        try:
            filename = os.path.basename(filepath)
            nums = re.findall(r'\d+', filename)
            if len(nums) < 2: continue
            
            l_val = int(nums[0])
            l_val -= 7 # 保留你代码中的逻辑
            thread_num = int(nums[1])
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                time_match = re.search(r'time:\s*(\d+)\s*us', content)
                op_match = re.search(r'op count:\s*(\d+)', content)
                
                if time_match:
                    time_val = int(time_match.group(1))
                    op_val = int(op_match.group(1)) if op_match else 0
                    
                    if thread_num not in data_map: data_map[thread_num] = {}
                    data_map[thread_num][l_val] = {'time': time_val, 'ops': op_val}
                    all_l_values.add(l_val)
                    all_threads.add(thread_num)
        except Exception:
            continue

    if not data_map:
        print("无有效数据")
        return

    # --- 3. 绘图逻辑 ---
    sorted_threads = sorted(list(all_threads))
    sorted_l_keys = sorted(list(all_l_values))
    
    x_indexes = np.arange(len(sorted_threads))
    total_width = 0.8
    bar_width = total_width / len(sorted_l_keys)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3), sharey=False)

    colors = [palette[2], palette[4], palette[1], palette[0]]

    for i, l_val in enumerate(sorted_l_keys):
        offset = (i - len(sorted_l_keys)/2) * bar_width + bar_width/2
        current_color = colors[i % len(colors)]
        
        y_times = []
        y_ops = []
        for t in sorted_threads:
            data = data_map.get(t, {}).get(l_val, {'time': 0, 'ops': 0})
            y_times.append(data['time'] / 1000.0)  # Convert from us to ms
            y_ops.append(data['ops'])
        
        # [修改点2] 绘制柱状图并保存返回值(rects)，用于标记数字
        rects1 = ax1.bar(x_indexes + offset, y_times, width=bar_width, 
                         label=f'$L$={l_val}', 
                         color=current_color, zorder=2)
        
        rects2 = ax2.bar(x_indexes + offset, y_ops, width=bar_width, 
                         color=current_color, zorder=2)

        # 添加数字标签 (fontsize设为16防止过大遮挡，fmt='%d'保留整数)
        # padding=3 让文字稍微高出柱子一点
        # ax1.bar_label(rects1, fmt='%d', label_type='edge', fontsize=16, padding=3)
        # ax2.bar_label(rects2, fmt='%d', label_type='edge', fontsize=16, padding=3)

    # --- 4. 样式与布局调整 ---
    
# 设置 Axis 1
    ax1.set_ylabel('Delay (ms)', fontsize=TEXT_SIZE_XYLABEL)
    apply_academic_style(ax1)
    ax1.set_xticks(x_indexes)
    ax1.set_xlabel('# of Threads', fontsize=TEXT_SIZE_XYLABEL)
    ax1.set_xticklabels(sorted_threads, fontsize=TEXT_SIZE_XYAXIS)
    ax1.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)
    ax1.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
    
    # [修改点] 增加 numticks=100，强制显示小刻度
    ax1.yaxis.set_minor_locator(LogLocator(base=10, subs=[2, 5], numticks=100))
    
    ax1.tick_params(axis='y', which='minor', length=4, width=1.5, left=True)
    # 设置 Axis 2
    ax2.set_ylabel('# of RefCnt Access', fontsize=TEXT_SIZE_XYLABEL)
    ax2.set_xlabel('# of Threads', fontsize=TEXT_SIZE_XYLABEL)
    ax2.set_xticks(x_indexes)
    ax2.set_xticklabels(sorted_threads, fontsize=TEXT_SIZE_XYAXIS)
    apply_academic_style(ax2)
    ax2.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)
    ax2.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)

    ax2.yaxis.set_minor_locator(LogLocator(base=10, subs=[2, 5], numticks=100))
    ax2.tick_params(axis='y', which='minor', length=4, width=1.5, left=True)

    # 图例设置 - 放在第一个图的左上方
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles, labels, 
               loc='upper left', 
               frameon=False, fontsize=TEXT_SIZE_LEGEND)

    plt.subplots_adjust(wspace=0.3)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plot_common.save_fig(script_dir, 'global_converge')
    plt.close()

if __name__ == "__main__":
    parse_and_plot_styled()