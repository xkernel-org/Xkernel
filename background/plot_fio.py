#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# MB/s
threshold_32_read_tpt = 28.1
threshold_128_read_tpt = 201
threshold_32_write_tpt = 3.8
threshold_128_write_tpt = 205

# Create bar chart
fig, ax = plt.subplots(1, 1, figsize=(6, 4))
categories = ['Read', 'Write']
# Reduce spacing between Read and Write categories
x = np.array([0, 0.6])  # Closer spacing between categories
width = 0.2
spacing = width  # Distance between centers of bars in the same category (bars will be adjacent)

# Data for bars
read_values = [threshold_32_read_tpt, threshold_128_read_tpt]
write_values = [threshold_32_write_tpt, threshold_128_write_tpt]

# Create bars for Read
bars_read_32 = ax.bar(x[0] - spacing/2, [threshold_32_read_tpt], width, label='value=32',
                      color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
bars_read_128 = ax.bar(x[0] + spacing/2, [threshold_128_read_tpt], width, label='value=128',
                       color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)

# Create bars for Write
bars_write_32 = ax.bar(x[1] - spacing/2, [threshold_32_write_tpt], width,
                       color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
bars_write_128 = ax.bar(x[1] + spacing/2, [threshold_128_write_tpt], width,
                        color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)

ax.set_ylabel('Throughput (MB/s)')
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.tick_params(axis='x', length=0)
ax.set_yticks(np.arange(0, 301, 100))
ax.legend(loc='upper left', ncol=2, frameon=True, facecolor='white', framealpha=1.0)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
# Make axis lines thicker
ax.spines['left'].set_linewidth(1)
ax.spines['bottom'].set_linewidth(1)

# Add value labels on bars
for bar, value in zip(bars_read_32, [threshold_32_read_tpt]):
    height = bar.get_height()
    x_pos = bar.get_x() + bar.get_width() / 2.0
    y_pos = height + 2  # Small offset above bar
    ax.text(x_pos, y_pos,
            f'{value:.1f}',
            ha='center', va='bottom', fontsize=20)
for bar, value in zip(bars_read_128, [threshold_128_read_tpt]):
    height = bar.get_height()
    x_pos = bar.get_x() + bar.get_width() / 2.0
    y_pos = height + 2  # Small offset above bar
    ax.text(x_pos, y_pos,
            f'{value:.0f}',
            ha='center', va='bottom', fontsize=20)
for bar, value in zip(bars_write_32, [threshold_32_write_tpt]):
    height = bar.get_height()
    x_pos = bar.get_x() + bar.get_width() / 2.0
    y_pos = height + 2  # Small offset above bar
    ax.text(x_pos, y_pos,
            f'{value:.1f}',
            ha='center', va='bottom', fontsize=20)
for bar, value in zip(bars_write_128, [threshold_128_write_tpt]):
    height = bar.get_height()
    x_pos = bar.get_x() + bar.get_width() / 2.0
    y_pos = height + 2  # Small offset above bar
    ax.text(x_pos, y_pos,
            f'{value:.0f}',
            ha='center', va='bottom', fontsize=20)

plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'fio_tpt')
plt.close(fig)
