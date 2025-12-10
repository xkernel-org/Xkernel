#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import matplotlib.pyplot as plt
import numpy as np
import plot_common

# Read and parse nvme_1.txt
with open('nvme_1.txt', 'r') as f:
    content_1 = f.read()
    
# Read and parse nvme_32.txt
with open('nvme_32.txt', 'r') as f:
    content_32 = f.read()

# Read and parse CPU files
with open('nvme_1_cpu.txt', 'r') as f:
    cpu_content_1 = f.read()
    
with open('nvme_32_cpu.txt', 'r') as f:
    cpu_content_32 = f.read()

# Extract ops/sec from nvme_1.txt
ops_match_1 = re.search(r'(\d+)\s+ops/sec', content_1)
ops_1 = int(ops_match_1.group(1)) if ops_match_1 else 0
ops_1 = ops_1 / 1000

# Extract ops/sec from nvme_32.txt
ops_match_32 = re.search(r'(\d+)\s+ops/sec', content_32)
ops_32 = int(ops_match_32.group(1)) if ops_match_32 else 0
ops_32 = ops_32 / 1000

# Extract percentiles from nvme_1.txt
p50_match_1 = re.search(r'P50:\s+([\d.]+)', content_1)
p75_match_1 = re.search(r'P75:\s+([\d.]+)', content_1)

p50_1 = float(p50_match_1.group(1)) if p50_match_1 else 0
p75_1 = float(p75_match_1.group(1)) if p75_match_1 else 0

# Extract percentiles from nvme_32.txt
p50_match_32 = re.search(r'P50:\s+([\d.]+)', content_32)
p75_match_32 = re.search(r'P75:\s+([\d.]+)', content_32)

p50_32 = float(p50_match_32.group(1)) if p50_match_32 else 0
p75_32 = float(p75_match_32.group(1)) if p75_match_32 else 0

# Extract CPU usage from nvme_1_cpu.txt
cpu_lines_1 = [line for line in cpu_content_1.split('\n') if line.strip() and 'CPU' not in line and (line.strip().startswith('08:') or line.strip()[0].isdigit())]
user_values_1 = []
sys_values_1 = []
iowait_values_1 = []
for line in cpu_lines_1:
    parts = line.split()
    if len(parts) >= 6 and parts[0].startswith('08:'):
        # Format: 08:46:55       5   23.17    0.00   36.59   40.24 ...
        user_values_1.append(float(parts[2]))
        sys_values_1.append(float(parts[4]))
        iowait_values_1.append(float(parts[5]))

user_1 = np.mean(user_values_1) if user_values_1 else 0
sys_1 = np.mean(sys_values_1) if sys_values_1 else 0
iowait_1 = np.mean(iowait_values_1) if iowait_values_1 else 0

# Extract CPU usage from nvme_32_cpu.txt
cpu_lines_32 = [line for line in cpu_content_32.split('\n') if line.strip() and 'CPU' not in line and (line.strip().startswith('08:') or line.strip()[0].isdigit())]
user_values_32 = []
sys_values_32 = []
iowait_values_32 = []
for line in cpu_lines_32:
    parts = line.split()
    if len(parts) >= 6 and parts[0].startswith('08:'):
        # Format: 08:44:22       5   20.00    0.00   28.24   51.76 ...
        user_values_32.append(float(parts[2]))
        sys_values_32.append(float(parts[4]))
        iowait_values_32.append(float(parts[5]))

user_32 = np.mean(user_values_32) if user_values_32 else 0
sys_32 = np.mean(sys_values_32) if sys_values_32 else 0
iowait_32 = np.mean(iowait_values_32) if iowait_values_32 else 0

# Second bar chart: Percentiles (P50, P75) (latency)
fig2, ax2 = plt.subplots(1, 1, figsize=(5, 4))
percentile_labels = ['P50', 'P75']
x = np.arange(len(percentile_labels))
width = 0.35

percentiles_1 = [p50_1, p75_1]
percentiles_32 = [p50_32, p75_32]

bars2_1 = ax2.bar(x - width/2, percentiles_1, width, label='value=1',
                  color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
bars2_32 = ax2.bar(x + width/2, percentiles_32, width, label='value=32',
                   color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)

ax2.set_ylabel('Latency (us)')
ax2.set_xticks(x)
ax2.set_xticklabels(percentile_labels)
ax2.tick_params(axis='x', length=0)
ax2.set_yticks(np.arange(0, 1051, 250))
ax2.set_ylim(0, 1050)
ax2.legend(frameon=True, facecolor='white', framealpha=1.0, fontsize=20)

# Remove top and right spines
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
# Make axis lines thicker
ax2.spines['left'].set_linewidth(1)
ax2.spines['bottom'].set_linewidth(1)

# Add value labels on bars
for bars, values in [(bars2_1, percentiles_1), (bars2_32, percentiles_32)]:
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                 f'{value:.0f}',
                 ha='center', va='bottom', fontsize=20)

plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'rocksdb_lat')
plt.close(fig2)

# Third bar chart: CPU usage (stacked)
fig3, ax3 = plt.subplots(1, 1, figsize=(5, 4))
cpu_categories = ['value=1', 'value=32']
# Use positions that give proper spacing between the two stacked bars
x_pos_1 = 0.25
x_pos_32 = 0.75
width_cpu = 0.25

# Stacked bar chart data
user_data = [user_1, user_32]
sys_data = [sys_1, sys_32]
iowait_data = [iowait_1, iowait_32]

# Create stacked bars for TS=1
bars3_user_1 = ax3.bar(x_pos_1, user_data[0], width_cpu, label='user',
                       color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
bars3_sys_1 = ax3.bar(x_pos_1, sys_data[0], width_cpu, bottom=user_data[0],
                      label='kernel', color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)
bars3_iowait_1 = ax3.bar(x_pos_1, iowait_data[0], width_cpu,
                         bottom=user_data[0] + sys_data[0],
                         label='iowait', color=plot_common.colors[0], edgecolor='black', linewidth=1, zorder=2)

# Create stacked bars for TS=32 with hatch
bars3_user_32 = ax3.bar(x_pos_32, user_data[1], width_cpu,
                        color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
bars3_sys_32 = ax3.bar(x_pos_32, sys_data[1], width_cpu, bottom=user_data[1],
                       color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)
bars3_iowait_32 = ax3.bar(x_pos_32, iowait_data[1], width_cpu,
                          bottom=user_data[1] + sys_data[1],
                          color=plot_common.colors[0], edgecolor='black', linewidth=1, zorder=2)

ax3.set_ylabel('CPU Usage (%)')
ax3.set_xticks([x_pos_1, x_pos_32])
ax3.set_xticklabels(cpu_categories)
ax3.tick_params(axis='x', length=0)
ax3.set_ylim(0, 100)
ax3.set_yticks([0, 25, 50, 75, 100])
ax3.legend(loc='center left', bbox_to_anchor=(0.95, 0.5), frameon=True, facecolor='white', framealpha=1.0, fontsize=16)

# Remove top and right spines
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
# Make axis lines thicker
ax3.spines['left'].set_linewidth(1)
ax3.spines['bottom'].set_linewidth(1)

# Add value labels on stacked bars
for i, (user_val, sys_val, iowait_val) in enumerate(zip(user_data, sys_data, iowait_data)):
    x_pos = x_pos_1 if i == 0 else x_pos_32
    # Label for user
    if user_val > 5:
        ax3.text(x_pos, user_val/2, f'{user_val:.0f}%', ha='center', va='center',
                 color='white', fontweight='bold', fontsize=20)
    # Label for sys
    if sys_val > 5:
        ax3.text(x_pos, user_val + sys_val/2, f'{sys_val:.0f}%', ha='center', va='center',
                 color='white', fontweight='bold', fontsize=20)
    # Label for iowait
    if iowait_val > 5:
        ax3.text(x_pos, user_val + sys_val + iowait_val/2, f'{iowait_val:.0f}%',
                 ha='center', va='center', color='white', fontweight='bold', fontsize=20)

plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'rocksdb_cpu')
plt.close(fig3)

