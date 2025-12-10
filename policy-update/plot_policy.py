#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.ticker import LogLocator, NullLocator, FuncFormatter

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Unified font sizes
TEXT_SIZE_XYLABEL = 18
TEXT_SIZE_XYAXIS = 18
TEXT_SIZE_TITLE = 17
TEXT_SIZE_TEXT = 18

# File paths
file_path_1 = './data-1.txt'
file_path_1_best = './data-1-best.txt'
file_path_15 = './data-15.txt'

def parse_latency_data(file_path):
    # (保持原有的解析函数不变)
    event_map = {
        'BPF_CHECK': 'BPF verify',
        'OPT_PREPARE': 'JMP-Prepare',
        'OPT_APPLY_BATCH': 'JMP-Apply',
        'REG_KPROBE': 'Kprobe Register',
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
data_1_best = parse_latency_data(file_path_1_best)
data_15 = parse_latency_data(file_path_15)

# 2. Prepare Data for Plotting
data_1['Kprobe Register'] = data_1['Kprobe Register'] + data_1['Kretprobe Reg']
data_1_best['Kprobe Register'] = data_1_best['Kprobe Register'] + data_1_best['Kretprobe Reg']
data_15['Kprobe Register'] = data_15['Kprobe Register'] + data_15['Kretprobe Reg']

# Merge JMP-Prepare and JMP-Apply into JMP Optimization
data_1['JMP Optimization'] = data_1['JMP-Prepare'] + data_1['JMP-Apply']
data_1_best['JMP Optimization'] = data_1_best['JMP-Prepare'] + data_1_best['JMP-Apply']
data_15['JMP Optimization'] = data_15['JMP-Prepare'] + data_15['JMP-Apply']

categories = ['BPF verify', 'JMP Optimization', 'Kprobe Register']
# x_labels = ['1 SS-Best', '1 SS-Worst', '15 SS-Worst']
x_labels = ['C1', 'C2', 'C3']

category_data = {}
for cat in categories:
    category_data[cat] = [data_1_best[cat], data_1[cat], data_15[cat]]

sum_data = [
    sum([data_1_best[cat] for cat in categories]),
    sum([data_1[cat] for cat in categories]),
    sum([data_15[cat] for cat in categories])
]
category_data['Sum'] = sum_data

# Round 15 SS data for the rightmost two subplots (Kprobe Register and Sum)
category_data['Kprobe Register'][2] = round(category_data['Kprobe Register'][2])
category_data['Sum'][2] = round(category_data['Sum'][2])

# 3. Plotting
# [修改1] 进一步压缩整体宽度
fig, axes = plt.subplots(1, 4, figsize=(8, 2))

palette = sns.color_palette("mako")
colors = [palette[5], palette[3], palette[2]]

# Compress x positions to reduce gap between bars
x_spacing = 0.35  # Reduce spacing between bar groups
x = np.arange(len(x_labels)) * x_spacing
width = 0.35

all_categories = categories + ['Sum']
for idx, cat in enumerate(all_categories):
    ax = axes[idx]
    vals = category_data[cat]
    
    bars = ax.bar(x, vals, width, color=colors, zorder=2)
    
    if idx == 0:
        ax.set_ylabel('Latency (ms)', fontsize=TEXT_SIZE_XYLABEL)
    else:
        ax.set_ylabel('')
        
    ax.set_title(cat, fontsize=TEXT_SIZE_TITLE, pad=10)  # Negative pad moves title upward
    ax.set_xticks(x)
    
    # [修改2] 旋转X轴标签 90度
    ax.set_xticklabels(x_labels, fontsize=TEXT_SIZE_XYAXIS, ha='center', va='top')
    
    ax.tick_params(axis='x', length=3, width=1, labelsize=TEXT_SIZE_XYAXIS)
    ax.tick_params(axis='y', length=3, width=1, labelsize=TEXT_SIZE_XYAXIS)
    
    if idx >= 2:
        ax.set_yscale('log')
        ax.yaxis.set_major_locator(LogLocator(base=10, subs=[1.0, 2.0, 5.0], numticks=10))
        ax.yaxis.set_minor_locator(NullLocator())
    
    ax.grid(True, which='both', alpha=0.3, axis='y', zorder=0)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)
    
    # Value labels
    for i, (bar, val) in enumerate(zip(bars, vals)):
        if val > 0:
            # Format: integer if whole number, otherwise one decimal place
            if val == int(val):
                val_str = f'{int(val)}'
            else:
                val_str = f'{val:.1f}'
            # [修改3] 旋转数值标签 90度
            # For the last bar, place label inside with light gray color
            is_last_bar = (i == len(bars) - 1)
            if is_last_bar:
                # For last two subplots (idx >= 2), place label lower
                if idx == 3:
                    y_pos = bar.get_height() / 16
                elif idx == 2:
                    y_pos = bar.get_height() / 20
                else:
                    y_pos = bar.get_height() / 2
                text_color = 'lightgray'
                va_align = 'center'
            else:
                y_pos = bar.get_height()
                text_color = 'black'
                va_align = 'bottom'
            ax.text(bar.get_x() + bar.get_width()/2, y_pos,
                   val_str,
                   ha='center', va=va_align, rotation=90,
                   fontsize=TEXT_SIZE_TEXT, fontweight='bold',
                   color=text_color)
    
    # Set y-axis ticks for first two subplots
    if idx == 0:
        ax.set_yticks([0, 2.5, 5])
        # Format y-axis labels: 0 as integer, others as one decimal
        def format_func(x, pos):
            if x == 0:
                return '0'
            else:
                return f'{x:.1f}'
        ax.yaxis.set_major_formatter(FuncFormatter(format_func))
    elif idx == 1:
        ax.set_yticks([0, 5, 10])

# [修改4] 调整布局参数，进一步压缩宽度
plt.tight_layout(pad=0.2, w_pad=0.1, h_pad=0.5)

script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'timeline_latency_bar')
plt.close()