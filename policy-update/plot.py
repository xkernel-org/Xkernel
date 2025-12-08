#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# File paths
file_path_1 = './data-1.txt'
file_path_15 = './data-15.txt'

def parse_latency_data(file_path):
    """
    Parses the specific log format and aggregates latency by category.
    Returns a dictionary with latency in ms.
    """
    event_map = {
        'BPF_CHECK': 'BPF verify',
        'OPT_PREPARE': 'JMP-Prepare',
        'OPT_APPLY_BATCH': 'JMP-Apply',
        'REG_KPROBE': 'Kprobe Reg',
        'REG_KRETPROBE': 'Kretprobe Reg'
    }
    
    stats = {v: 0.0 for v in event_map.values()}
    
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found.")
        return stats

    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 3 or 'PID' in line or 'Tracing' in line:
            continue
            
        event = parts[1]
        
        try:
            val = float(parts[-2])
            unit = parts[-1]
        except ValueError:
            continue
            
        if event in event_map:
            category = event_map[event]
            if unit == 'us':
                stats[category] += val / 1000.0
            elif unit == 'ms':
                stats[category] += val
            elif unit == 's':
                stats[category] += val * 1000.0
                
    return stats

# 1. Parse Data
data_1 = parse_latency_data(file_path_1)
data_15 = parse_latency_data(file_path_15)

# 2. Prepare Data for Plotting
labels = ['1 CS', '15 CS']
stack_categories = ['BPF verify', 'JMP-Prepare', 'JMP-Apply', 'Kprobe Reg', 'Kretprobe Reg']

category_values = []
for cat in stack_categories:
    category_values.append([data_1[cat], data_15[cat]])

# 3. Plotting
fig, ax = plt.subplots(1, 1, figsize=(8, 4))

# --- 设置 X 轴为对数坐标 (横向图) ---
ax.set_xscale('log')
ax.set_xlim(left=1, right=1e3) 
# ----------------------------------

colors = [plot_common.colors[1], plot_common.colors[4], plot_common.colors[0], plot_common.colors[2], plot_common.colors[3]]

y = np.arange(len(labels))
bar_height = 0.45 
left_pos = np.zeros(len(labels))

bars_list = []

for i, cat in enumerate(stack_categories):
    vals = category_values[i]
    # 使用 barh 绘制横向柱状图
    bar = ax.barh(y, width=vals, height=bar_height, left=left_pos, label=cat,
                  color=colors[i], edgecolor='black', linewidth=1, zorder=2)
    bars_list.append(bar)
    left_pos += vals 

# 4. Styling
ax.set_xlabel('Latency (ms)')
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.tick_params(axis='y', length=0, width=0)
ax.tick_params(axis='x', length=10, width=2)

# 反转Y轴，让 CS=1 在上方
ax.invert_yaxis()

# Grid 设置
ax.grid(True, which='both', alpha=0.3, axis='x', zorder=0)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1)
ax.spines['bottom'].set_linewidth(1)

# --- 关键修改：图例移动回图内右上角 ---
ax.legend(
    frameon=True,
    facecolor='white',
    framealpha=1,
    loc='upper right',  # 改为右上角
    ncol=2
)
# -----------------------------------

# 标注总数值（位于柱状图右侧）
for i in range(len(labels)):
    total_width = left_pos[i]
    if total_width > 0:
        ax.text(total_width * 1.1, y[i], 
                f'{total_width:.1f}', 
                ha='left', 
                va='center', 
                color='black', 
                fontweight='bold')

plt.tight_layout()

script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'timeline_latency_bar')
plt.close()