#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec  # Import GridSpec for fine-grained layout control
import seaborn as sns

# Assume plot_common is available in this environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

TEXT_SIZE = 18

# Text sizes
TEXT_SIZE_XYLABEL = 20
TEXT_SIZE_XYAXIS = 20
TEXT_SIZE_LEGEND = 20

# Tick parameters
TICK_LENGTH_X = 5  # Set to 0 to hide ticks, or a positive value to show ticks
TICK_WIDTH_X = 1

palette = sns.color_palette("rocket")
user_color = palette[2]
kernel_color = palette[3]
iowait_color = palette[4]
palette = sns.color_palette("mako")
COLOR_128 = palette[2]
COLOR_32 = palette[3]
COLOR_1 = palette[5]

# ==========================================
# 1. Data preparation
# ==========================================

script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'results')


def parse_hdd_log(path):
    """Extract BW (MiB/s) from fio_bench summary log."""
    with open(path) as f:
        for line in f:
            m = re.match(r'\s*BW\s*:\s*([\d.]+)\s*MiB/s', line)
            if m:
                return float(m.group(1))
    return 0


# --- Part A: Throughput data (from HDD results) ---
try:
    t_32_read  = parse_hdd_log(os.path.join(results_dir, 'hdd_32_read.txt'))
    t_128_read = parse_hdd_log(os.path.join(results_dir, 'hdd_128_read.txt'))
    t_32_write  = parse_hdd_log(os.path.join(results_dir, 'hdd_32_write.txt'))
    t_128_write = parse_hdd_log(os.path.join(results_dir, 'hdd_128_write.txt'))
except FileNotFoundError as e:
    print(f"Warning: HDD log not found ({e}). Using dummy data.", file=sys.stderr)
    t_32_read, t_128_read = 28.1, 201
    t_32_write, t_128_write = 3.8, 205

tp_values_32 = [t_32_read, t_32_write]
tp_values_128 = [t_128_read, t_128_write]
tp_labels = ['Read', 'Write']

# --- Part B: Latency and CPU data (from NVMe results) ---
try:
    with open(os.path.join(results_dir, 'nvme_1.txt'), 'r') as f: content_1 = f.read()
    with open(os.path.join(results_dir, 'nvme_32.txt'), 'r') as f: content_32 = f.read()
    with open(os.path.join(results_dir, 'nvme_1_cpu.txt'), 'r') as f: cpu_content_1 = f.read()
    with open(os.path.join(results_dir, 'nvme_32_cpu.txt'), 'r') as f: cpu_content_32 = f.read()

    # Extract percentiles
    p50_match_1 = re.search(r'P50:\s+([\d.]+)', content_1)
    p75_match_1 = re.search(r'P75:\s+([\d.]+)', content_1)
    p50_1 = float(p50_match_1.group(1)) if p50_match_1 else 0
    p75_1 = float(p75_match_1.group(1)) if p75_match_1 else 0

    p50_match_32 = re.search(r'P50:\s+([\d.]+)', content_32)
    p75_match_32 = re.search(r'P75:\s+([\d.]+)', content_32)
    p50_32 = float(p50_match_32.group(1)) if p50_match_32 else 0
    p75_32 = float(p75_match_32.group(1)) if p75_match_32 else 0

    # Extract CPU usage Helper
    def get_avg_cpu(content):
        cpu_lines = [line for line in content.split('\n') if line.strip() and 'CPU' not in line and (line.strip().startswith('08:') or line.strip()[0].isdigit())]
        u_vals, s_vals, w_vals = [], [], []
        for line in cpu_lines:
            parts = line.split()
            if len(parts) >= 6:
                u_vals.append(float(parts[2]))
                s_vals.append(float(parts[4]))
                w_vals.append(float(parts[5]))
        return (np.mean(u_vals) if u_vals else 0, 
                np.mean(s_vals) if s_vals else 0, 
                np.mean(w_vals) if w_vals else 0)

    user_1, sys_1, iowait_1 = get_avg_cpu(cpu_content_1)
    user_32, sys_32, iowait_32 = get_avg_cpu(cpu_content_32)

except FileNotFoundError:
    print("Warning: Log files not found. Using dummy data.")
    p50_1, p75_1, p50_32, p75_32 = 100, 150, 200, 250
    user_1, sys_1, iowait_1 = 10, 20, 5
    user_32, sys_32, iowait_32 = 15, 25, 10

# ==========================================
# 2. Plot setup
# ==========================================

fig = plt.figure(figsize=(11.5, 3))

# --- Layout adjustment ---
# Use nested GridSpec to keep the two right-side plots close together.
# Outer grid: split the canvas into [left, (middle + right)].
# width_ratios=[1, 2.2]: make the right region wider because it contains two subplots.
# wspace=0.5: increase spacing between the left plot and the right-side region.
gs_outer = fig.add_gridspec(1, 2, width_ratios=[1, 2.2], wspace=0.4)

# Inner grid: split the right-side region into [middle, right].
# wspace=0.5: increase spacing between the middle and right plots.
gs_inner = gs_outer[1].subgridspec(1, 2, width_ratios=[1, 1], wspace=0.65)

# Create axes
ax1 = fig.add_subplot(gs_outer[0]) # Left plot (Throughput)
ax2 = fig.add_subplot(gs_inner[0]) # Middle plot (Latency)
ax3 = fig.add_subplot(gs_inner[1]) # Right plot (CPU); height is adjusted later

# Common style variables
common_width = 0.18       
group_spacing = 0.45      

# ----------------------------------------------------------------
# --- Figure 1: Throughput ---
# ----------------------------------------------------------------
x_tp = np.array([0, group_spacing]) 
width_tp = common_width

rects1 = ax1.bar(x_tp - width_tp/2, tp_values_32, width_tp, label='32', color=COLOR_32, zorder=2)
rects2 = ax1.bar(x_tp + width_tp/2, tp_values_128, width_tp, label='128', color=COLOR_128, zorder=2)

ax1.set_ylabel('Tput. (MB/s)', fontsize=TEXT_SIZE_XYLABEL)

ax1.set_xticks(x_tp)
ax1.set_xticklabels(tp_labels, fontsize=TEXT_SIZE_XYAXIS)
ax1.set_yticks([0, 100, 200])
ax1.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
ax1.set_ylim(0, 250)
ax1.set_xlim(-0.3, group_spacing + 0.3)

# Remove downward x-axis tick marks while keeping labels
ax1.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X)

# Remove top and right spines
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

for rect in rects1 + rects2:
    height = rect.get_height()
    ax1.text(rect.get_x() + rect.get_width()/2, height + 2,
             f'{height}', ha='center', va='bottom', fontsize=TEXT_SIZE, rotation=90)

# ----------------------------------------------------------------
# --- Figure 2: Latency ---
# ----------------------------------------------------------------
percentile_labels = ['P50', 'P75']
x_lat = np.array([0, group_spacing]) 
width_lat = common_width

lat_1 = [p50_1, p75_1]
lat_32 = [p50_32, p75_32]

bars2_1 = ax2.bar(x_lat - width_lat/2, lat_1, width_lat, label='1',
                  color=COLOR_1, zorder=2)
bars2_32 = ax2.bar(x_lat + width_lat/2, lat_32, width_lat, label='32',
                   color=COLOR_32, zorder=2)

ax2.set_ylabel('Latency (us)', fontsize=TEXT_SIZE_XYLABEL)

ax2.set_xticks(x_lat)
ax2.set_xticklabels(percentile_labels, fontsize=TEXT_SIZE_XYAXIS)
lat_max = max(lat_1 + lat_32)
lat_ylim = int(lat_max * 1.25)
ax2.set_yticks([0, lat_ylim, lat_ylim//2])
ax2.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
ax2.set_ylim(0, lat_ylim)
ax2.set_xlim(-0.3, group_spacing + 0.3) 
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# Remove downward x-axis tick marks
ax2.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X)

for bars, values in [(bars2_1, lat_1), (bars2_32, lat_32)]:
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 10,
                 f'{value:.0f}', ha='center', va='bottom', fontsize=TEXT_SIZE, rotation=90)

# ----------------------------------------------------------------
# --- Figure 3: CPU Usage ---
# ----------------------------------------------------------------
cpu_categories = ['V=1', 'V=32']
x_cpu = np.array([0, group_spacing]) 
width_cpu = 0.3

user_data = [user_1, user_32]
sys_data = [sys_1, sys_32]
iowait_data = [iowait_1, iowait_32]

user_hatch = "///"
kernel_hatch = "\\\\"
iowait_hatch = "x"

# Stacked Bar 1 (value=1) - using hatch instead of color
ax3.bar(x_cpu[0], user_data[0], width_cpu, label='user',
         hatch=user_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")
ax3.bar(x_cpu[0], sys_data[0], width_cpu, bottom=user_data[0],
        label='kernel',  hatch=kernel_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")
ax3.bar(x_cpu[0], iowait_data[0], width_cpu, bottom=user_data[0] + sys_data[0],
        label='iowait',  hatch=iowait_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")

# Stacked Bar 2 (value=32) - using hatch instead of color
ax3.bar(x_cpu[1], user_data[1], width_cpu,
         hatch=user_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")
ax3.bar(x_cpu[1], sys_data[1], width_cpu, bottom=user_data[1],
         hatch=kernel_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")
ax3.bar(x_cpu[1], iowait_data[1], width_cpu, bottom=user_data[1] + sys_data[1],
         hatch=iowait_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")

ax3.set_ylabel('CPU Usage (%)', fontsize=TEXT_SIZE_XYLABEL)
ax3.set_xticks(x_cpu)
ax3.set_xticklabels(cpu_categories, fontsize=TEXT_SIZE_XYAXIS)
ax3.set_yticks([0, 50, 100])
ax3.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
ax3.set_ylim(0, 100)
ax3.set_xlim(-0.3, group_spacing + 0.3) 
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)

# Remove downward x-axis tick marks
ax3.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X)

# Value labels - using black text since background is white
# for i, (user_val, sys_val, iowait_val) in enumerate(zip(user_data, sys_data, iowait_data)):
#     pos = x_cpu[i]
#     if user_val > 8:
#         ax3.text(pos, user_val/2, f'{user_val:.0f}%', ha='center', va='center', color='black', fontweight='bold', fontsize=TEXT_SIZE)
#     if sys_val > 8:
#         ax3.text(pos, user_val + sys_val/2, f'{sys_val:.0f}%', ha='center', va='center', color='black', fontweight='bold', fontsize=TEXT_SIZE)
#     if iowait_val > 8:
#         ax3.text(pos, user_val + sys_val + iowait_val/2, f'{iowait_val:.0f}%', ha='center', va='center', color='black', fontweight='bold', fontsize=TEXT_SIZE)

# ----------------------------------------------------------------
# --- Unified legend (placed at the top) ---
# ----------------------------------------------------------------
# Get handles and labels from all axes
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
h3, l3 = ax3.get_legend_handles_labels()

# Merge legend entries, including 1, 32, 128, and CPU legend entries
# Ensure order: 1, 32, 128, user, kernel, iowait
all_handles = []
all_labels = []

# Get '1' and '32' from the latency plot
for handle, label in zip(h2, l2):
    if label == '1':
        all_handles.append(handle)
        all_labels.append('1')
    elif label == '32':
        all_handles.append(handle)
        all_labels.append('32')

# Get '32' and '128' from the throughput plot, but add only the missing '128'
for handle, label in zip(h1, l1):
    if label == '128':
        all_handles.append(handle)
        all_labels.append('128')

# Create a shared legend showing 1, 32, and 128 (excluding user, kernel, and iowait)
# Mark 32 as the default
all_labels[all_labels.index('32')] = '32 (default)'
fig.legend(all_handles, all_labels, loc='upper center', bbox_to_anchor=(0.5, 1.1),
           ncol=3, frameon=False, fontsize=TEXT_SIZE_LEGEND)

# Create a separate legend for ax3 above the subplot
cpu_handles = []
cpu_labels = []
seen_cpu_labels = set()
for handle, label in zip(h3, l3):
    if label not in seen_cpu_labels:
        cpu_handles.append(handle)
        cpu_labels.append(label)
        seen_cpu_labels.add(label)
ax3.legend(cpu_handles, cpu_labels, loc='upper center', bbox_to_anchor=(0.49, 1.8),
           ncol=1, frameon=False, fontsize=TEXT_SIZE_LEGEND)

# Adjust layout; rect reserves top space for the legend [left, bottom, right, top]
# Increase top margin from 0.92 to 0.88 so the legend remains visible
import warnings
warnings.filterwarnings("ignore", message=".*tight_layout.*")
plt.tight_layout(rect=[0, 0, 1, 0.88])

# Adjust ax3 height so it is shorter than ax2 while bottom-aligned with ax1 and ax2
ax1_bbox = ax1.get_position()
ax2_bbox = ax2.get_position()
ax3_bbox = ax3.get_position()
# Set ax3 height to 70% of ax2 while keeping the bottoms aligned
height_ratio = 0.7
new_height = ax2_bbox.height * height_ratio
# Bottom alignment: ax3's y0 should match ax2's y0
new_bottom = ax2_bbox.y0
ax3.set_position([ax3_bbox.x0, new_bottom, ax3_bbox.width, new_height])

# Draw a gray solid separator between the leftmost and middle plots
# Get the positions of both axes after tight_layout
ax1_bbox = ax1.get_position()
ax2_bbox = ax2.get_position()
# Compute the separator x position at the midpoint between the two plots
x_line = (ax1_bbox.x1 + ax2_bbox.x0) / 2 - 0.047
# Draw the line in figure coordinates
fig.add_artist(plt.Line2D([x_line, x_line], [ax1_bbox.y0-0.09, ax1_bbox.y1+0.04], 
                          color='gray', linewidth=3, transform=fig.transFigure))

SUBFIG_SPACE = 0.2
SUBFIG_TEXT_SIZE =26

# Add subplot labels in USENIX style (Times New Roman font)
# Use matplotlib's textpath to measure text width accurately
from matplotlib.textpath import TextPath
from matplotlib import font_manager

# Label for left subplot - centered below ax1
ax1_bbox = ax1.get_position()
label_x = ax1_bbox.x0 + ax1_bbox.width / 2  # Center of ax1
label_y = ax1_bbox.y0 - SUBFIG_SPACE

# Measure widths using TextPath
prop = font_manager.FontProperties(family='Times New Roman', size=SUBFIG_TEXT_SIZE)
# Measure the full text to get accurate total width
path_a_full = TextPath((0, 0), '(a) FIO on HDD', prop=prop, size=SUBFIG_TEXT_SIZE)
path_a_label = TextPath((0, 0), '(a) ', prop=prop, size=SUBFIG_TEXT_SIZE)
bbox_a_full = path_a_full.get_extents()
bbox_a_label = path_a_label.get_extents()
total_width_a = bbox_a_full.width / fig.dpi / fig.get_figwidth()
width_a_label = bbox_a_label.width / fig.dpi / fig.get_figwidth()

# Draw "(a) " without bold - start from left edge of centered text
fig.text(label_x - total_width_a-0.14, label_y + 0.01, '(a) ', 
         ha='left', va='top', fontsize=SUBFIG_TEXT_SIZE, 
         family='Times New Roman', weight='normal')
# Draw "FIO on HDD" with bold - positioned right after "(a) "
fig.text(label_x - total_width_a-0.14 + width_a_label+0.05, label_y, 'FIO on HDD', 
         ha='left', va='top', fontsize=SUBFIG_TEXT_SIZE, 
         family='Times New Roman', weight='normal')

# Label for right two subplots - centered below ax2 and ax3
ax2_bbox = ax2.get_position()
ax3_bbox = ax3.get_position()
# Calculate the center x position between ax2 and ax3
center_x = (ax2_bbox.x0 + ax3_bbox.x1) / 2
# Use the bottom of ax2 (or ax3, they should be aligned)
bottom_y = ax2_bbox.y0 - SUBFIG_SPACE

# Measure widths for "(b) RocksDB on NVMe SSD"
# Measure the full text to get accurate total width
path_b_full = TextPath((0, 0), '(b) RocksDB on NVMe SSD', prop=prop, size=SUBFIG_TEXT_SIZE)
path_b_label = TextPath((0, 0), '(b) ', prop=prop, size=SUBFIG_TEXT_SIZE)
bbox_b_full = path_b_full.get_extents()
bbox_b_label = path_b_label.get_extents()
total_width_b = bbox_b_full.width / fig.dpi / fig.get_figwidth()
width_b_label = bbox_b_label.width / fig.dpi / fig.get_figwidth()

# Draw "(b) " without bold - start from left edge of centered text
fig.text(center_x - total_width_b - 0.22, bottom_y + 0.01, '(b) ', 
         ha='left', va='top', fontsize=SUBFIG_TEXT_SIZE, 
         family='Times New Roman', weight='normal')
# Draw "RocksDB on NVMe SSD" with bold - positioned right after "(b) "
fig.text(center_x - total_width_b- 0.22 + width_b_label+0.05, bottom_y, 'RocksDB on NVMe SSD', 
         ha='left', va='top', fontsize=SUBFIG_TEXT_SIZE, 
         family='Times New Roman', weight='normal')

script_dir_out = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir_out, 'figure1')
# plt.show()
