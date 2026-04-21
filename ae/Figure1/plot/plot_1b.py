#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot Figure 1(b): RocksDB on NVMe SSD — Latency + CPU (V=1 vs V=32)."""
import re
import sys
import os
import warnings
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

TEXT_SIZE = 18
TEXT_SIZE_XYLABEL = 20
TEXT_SIZE_XYAXIS = 20
TEXT_SIZE_LEGEND = 20
TICK_LENGTH_X = 5
TICK_WIDTH_X = 1

palette = sns.color_palette("mako")
COLOR_32 = palette[3]
COLOR_1 = palette[5]

script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'results')

# ── Load data ────────────────────────────────────────────────────────
try:
    with open(os.path.join(results_dir, 'nvme_1.txt')) as f: content_1 = f.read()
    with open(os.path.join(results_dir, 'nvme_32.txt')) as f: content_32 = f.read()
    with open(os.path.join(results_dir, 'nvme_1_cpu.txt')) as f: cpu_content_1 = f.read()
    with open(os.path.join(results_dir, 'nvme_32_cpu.txt')) as f: cpu_content_32 = f.read()

    p50_match_1 = re.search(r'P50:\s+([\d.]+)', content_1)
    p75_match_1 = re.search(r'P75:\s+([\d.]+)', content_1)
    p50_1 = float(p50_match_1.group(1)) if p50_match_1 else 0
    p75_1 = float(p75_match_1.group(1)) if p75_match_1 else 0

    p50_match_32 = re.search(r'P50:\s+([\d.]+)', content_32)
    p75_match_32 = re.search(r'P75:\s+([\d.]+)', content_32)
    p50_32 = float(p50_match_32.group(1)) if p50_match_32 else 0
    p75_32 = float(p75_match_32.group(1)) if p75_match_32 else 0

    def get_avg_cpu(content):
        cpu_lines = [line for line in content.split('\n')
                     if line.strip() and 'CPU' not in line
                     and (line.strip().startswith('08:') or line.strip()[0].isdigit())]
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
    print("Warning: NVMe log files not found. Using dummy data.", file=sys.stderr)
    p50_1, p75_1, p50_32, p75_32 = 100, 150, 200, 250
    user_1, sys_1, iowait_1 = 10, 20, 5
    user_32, sys_32, iowait_32 = 15, 25, 10

# ── Summary table ────────────────────────────────────────────────────
print()
print("=" * 58)
print(f"  {'Metric':<22} {'V=32 (default)':>14}  {'V=1 (tuned)':>14}")
print("-" * 58)
print(f"  {'P50 latency (µs)':<22} {p50_32:>14.1f}  {p50_1:>14.1f}")
print(f"  {'P75 latency (µs)':<22} {p75_32:>14.1f}  {p75_1:>14.1f}")
print(f"  {'P50 reduction':<22} {f'{p50_32/max(p50_1,0.1):.2f}×':>14}")
print(f"  {'P75 reduction':<22} {f'{p75_32/max(p75_1,0.1):.2f}×':>14}")
print(f"  {'%user':<22} {user_32:>14.1f}  {user_1:>14.1f}")
print(f"  {'%kernel':<22} {sys_32:>14.1f}  {sys_1:>14.1f}")
print(f"  {'%iowait':<22} {iowait_32:>14.1f}  {iowait_1:>14.1f}")
print(f"  {'iowait Δ':<22} {f'{iowait_32-iowait_1:+.1f}%':>14}")
print("=" * 58)

# ── Plot ─────────────────────────────────────────────────────────────
fig, (ax_lat, ax_cpu) = plt.subplots(1, 2, figsize=(7, 3.5),
                                      gridspec_kw={'width_ratios': [1, 1], 'wspace': 0.55})

common_width = 0.18
group_spacing = 0.45

# ── Latency ──────────────────────────────────────────────────────────
percentile_labels = ['P50', 'P75']
x_lat = np.array([0, group_spacing])

lat_1 = [p50_1, p75_1]
lat_32 = [p50_32, p75_32]

bars_1 = ax_lat.bar(x_lat - common_width/2, lat_1, common_width,
                     label='1', color=COLOR_1, zorder=2)
bars_32 = ax_lat.bar(x_lat + common_width/2, lat_32, common_width,
                      label='32', color=COLOR_32, zorder=2)

ax_lat.set_ylabel('Latency (us)', fontsize=TEXT_SIZE_XYLABEL)
ax_lat.set_xticks(x_lat)
ax_lat.set_xticklabels(percentile_labels, fontsize=TEXT_SIZE_XYAXIS)
lat_max = max(lat_1 + lat_32)
lat_ylim = int(lat_max * 1.25)
ax_lat.set_yticks([0, lat_ylim])
ax_lat.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
ax_lat.set_ylim(0, lat_ylim)
ax_lat.set_xlim(-0.3, group_spacing + 0.3)
ax_lat.spines['top'].set_visible(False)
ax_lat.spines['right'].set_visible(False)
ax_lat.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X)

for bars, values in [(bars_1, lat_1), (bars_32, lat_32)]:
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax_lat.text(bar.get_x() + bar.get_width()/2., height + 10,
                    f'{value:.0f}', ha='center', va='bottom',
                    fontsize=TEXT_SIZE, rotation=90)

# ── CPU Usage (stacked bar) ──────────────────────────────────────────
cpu_categories = ['V=1', 'V=32']
x_cpu = np.array([0, group_spacing])
width_cpu = 0.3

user_data = [user_1, user_32]
sys_data = [sys_1, sys_32]
iowait_data = [iowait_1, iowait_32]

user_hatch = "///"
kernel_hatch = "\\\\"
iowait_hatch = "x"

ax_cpu.bar(x_cpu[0], user_data[0], width_cpu, label='user',
           hatch=user_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")
ax_cpu.bar(x_cpu[0], sys_data[0], width_cpu, bottom=user_data[0],
           label='kernel', hatch=kernel_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")
ax_cpu.bar(x_cpu[0], iowait_data[0], width_cpu, bottom=user_data[0] + sys_data[0],
           label='iowait', hatch=iowait_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")

ax_cpu.bar(x_cpu[1], user_data[1], width_cpu,
           hatch=user_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")
ax_cpu.bar(x_cpu[1], sys_data[1], width_cpu, bottom=user_data[1],
           hatch=kernel_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")
ax_cpu.bar(x_cpu[1], iowait_data[1], width_cpu, bottom=user_data[1] + sys_data[1],
           hatch=iowait_hatch, zorder=2, edgecolor='black', linewidth=1, color="white")

ax_cpu.set_ylabel('CPU Usage (%)', fontsize=TEXT_SIZE_XYLABEL)
ax_cpu.set_xticks(x_cpu)
ax_cpu.set_xticklabels(cpu_categories, fontsize=TEXT_SIZE_XYAXIS)
ax_cpu.set_yticks([0, 50, 100])
ax_cpu.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
ax_cpu.set_ylim(0, 100)
ax_cpu.set_xlim(-0.3, group_spacing + 0.3)
ax_cpu.spines['top'].set_visible(False)
ax_cpu.spines['right'].set_visible(False)
ax_cpu.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X)

# ── Legends ──────────────────────────────────────────────────────────
h_lat, l_lat = ax_lat.get_legend_handles_labels()
l_lat[l_lat.index('32')] = '32 (default)'
fig.legend(h_lat, l_lat, loc='upper left', bbox_to_anchor=(0.05, 1.08),
           ncol=2, frameon=False, fontsize=TEXT_SIZE_LEGEND)

h_cpu, l_cpu = ax_cpu.get_legend_handles_labels()
ax_cpu.legend(h_cpu, l_cpu, loc='upper center', bbox_to_anchor=(0.5, 1.35),
              ncol=1, frameon=False, fontsize=TEXT_SIZE_LEGEND)

# Shrink ax_cpu height to 70% of ax_lat (CPU percentages are bounded)
warnings.filterwarnings("ignore", message=".*tight_layout.*")
plt.tight_layout(rect=[0, 0, 1, 0.9])

lat_bbox = ax_lat.get_position()
cpu_bbox = ax_cpu.get_position()
new_height = lat_bbox.height * 0.7
ax_cpu.set_position([cpu_bbox.x0, lat_bbox.y0, cpu_bbox.width, new_height])

plot_common.save_fig(script_dir, 'figure1b')
plt.close(fig)
