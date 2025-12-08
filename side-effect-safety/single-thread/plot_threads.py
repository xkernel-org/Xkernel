#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import plot_common

# Read data from threads.txt
threads = []
delay_min = []
delay_max = []

with open('threads.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # Format: delay_min/delay_max, rate/s, threads
        parts = line.split(',')
        delay_part = parts[0].strip()
        threads_part = int(parts[2].strip())
        
        # Parse delay_min/delay_max
        delay_values = delay_part.split('/')
        min_val = int(delay_values[0])
        max_val = int(delay_values[1])
        
        threads.append(threads_part)
        delay_min.append(min_val)
        delay_max.append(max_val)

# Convert from nanoseconds to milliseconds
delay_min = [val / 1000000.0 for val in delay_min]
delay_max = [val / 1000000.0 for val in delay_max]

# Create bar chart
fig, ax = plt.subplots(1, 1, figsize=(8, 3.6))
x = np.arange(len(threads))
width = 0.35

# Create bars
bars_min = ax.bar(x - width/2, delay_min, width, label='Fastest Task',
                  color=plot_common.colors[1], edgecolor='black', linewidth=1, zorder=2)
bars_max = ax.bar(x + width/2, delay_max, width, label='Slowest Task',
                  color=plot_common.colors[0], edgecolor='black', linewidth=1, zorder=2)

ax.set_ylabel('Delay (ms)')
ax.set_xlabel('# of Threads')
ax.set_xticks(x)
ax.set_xticklabels(threads)
ax.set_yticks([0, 2, 4, 6, 8, 10])
ax.set_ylim(0, 10)
ax.tick_params(axis='x', length=0)
ax.legend(loc='best', frameon=True, facecolor='white', framealpha=1.0)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
# Make axis lines thicker
ax.spines['left'].set_linewidth(1)
ax.spines['bottom'].set_linewidth(1)

# Add value labels on bars
for bar, value in zip(bars_min, delay_min):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{value:.1f}',
            ha='center', va='bottom')
for bar, value in zip(bars_max, delay_max):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{value:.1f}',
            ha='center', va='bottom')

plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'threads')
plt.close(fig)

