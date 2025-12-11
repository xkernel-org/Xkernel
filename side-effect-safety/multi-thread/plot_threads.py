#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import seaborn as sns

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import plot_common

# Unified color palette
palette = sns.color_palette("mako")

# Text sizes
TEXT_SIZE_XYLABEL = 13
TEXT_SIZE_XYAXIS = 13
TEXT_SIZE_LEGEND = 13

# Tick parameters
TICK_LENGTH_X = 5
TICK_WIDTH_X = 1

# Read data from case files
cases = ['cases1', 'cases2', 'cases3', 'cases4']
threads = [1, 4, 16]  # Only 1, 4, 16 for multi-thread
case_data = {}  # {case_name: {thread_count: {'min': val, 'avg': val, 'max': val}}}

for case_name in cases:
    case_data[case_name] = {}
    filename = f'{case_name}.txt'
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Skip function name lines (contain addresses like 0x...)
            if '0x' in line:
                continue
            # Format: delay_min/delay_avg/delay_max, thread_count
            if '/' in line and ',' in line:
                parts = line.split(',')
                delay_part = parts[0].strip()
                threads_part = int(parts[-1].strip())  # Use last part as thread count
                
                # Only process lines with matching thread counts
                if threads_part in threads:
                    # Parse delay_min/delay_avg/delay_max
                    delay_values = delay_part.split('/')
                    if len(delay_values) >= 3:
                        min_val = int(delay_values[0])
                        avg_val = int(delay_values[1])
                        max_val = int(delay_values[2])
                        
                        # Convert from nanoseconds to milliseconds
                        case_data[case_name][threads_part] = {
                            'min': min_val / 1000000.0,
                            'avg': avg_val / 1000000.0,
                            'max': max_val / 1000000.0
                        }

# Create bar chart
fig, ax = plt.subplots(1, 1, figsize=(4.5, 2.3))
x = np.arange(len(cases))
n_threads = len(threads)
width = 0.8 / n_threads  # Width for each bar

# Plot bars for each thread count
for i, thread_count in enumerate(threads):
    # Extract data for this thread count across all cases
    min_vals = [case_data[case_name][thread_count]['min'] for case_name in cases]
    avg_vals = [case_data[case_name][thread_count]['avg'] for case_name in cases]
    max_vals = [case_data[case_name][thread_count]['max'] for case_name in cases]
    
    # Use average as center values, calculate error ranges
    # Ensure all values are positive and properly ordered
    center_vals = []
    yerr_lower = []
    yerr_upper = []
    for j in range(len(cases)):
        min_val = min(min_vals[j], avg_vals[j], max_vals[j])  # Ensure min is actually the minimum
        max_val = max(min_vals[j], avg_vals[j], max_vals[j])  # Ensure max is actually the maximum
        avg_val = avg_vals[j]  # Use the average as center
        
        center_vals.append(avg_val)
        yerr_lower.append(max(0, avg_val - min_val))  # Ensure positive
        yerr_upper.append(max(0, max_val - avg_val))  # Ensure positive
    
    # Calculate x positions for this thread count
    offset = (i - n_threads / 2 + 0.5) * width
    
    # Plot bars with error bars
    bars = ax.bar(x + offset, center_vals, width, 
                  label=f'{thread_count} threads',
                  color=palette[5-i-2], zorder=2)
    
    # Add error bars
    ax.errorbar(x + offset, center_vals, 
                yerr=[yerr_lower, yerr_upper],
                fmt='none', color='black', capsize=3, capthick=1.5, 
                elinewidth=1.5, zorder=3)
    
    # Add value labels on bars (show max value at top, rotated 90 degrees)
    for j, (bar, max_val) in enumerate(zip(bars, max_vals)):
        height = bar.get_height()
        if max_val > 0.1:  # Only label if value is large enough
            ax.text(bar.get_x() + bar.get_width()/2., max_val + 0.5,
                    f'{max_val:.1f}',
                    ha='center', va='bottom', fontsize=TEXT_SIZE_XYAXIS, rotation=90)

# Create labels with trigger frequency annotations and SS values
ss_values = [1, 2, 4, 4]

xlabels = ['1K trig/s\n1SS', '10K trig/s\n2SS', '100K trig/s\n4SS', '1M trig/s\n4SS']   

# Set empty ylabel to preserve padding space
ax.set_ylabel('', fontsize=TEXT_SIZE_XYLABEL)
ax.set_yticks([0, 5, 10, 15, 20])
ax.set_ylim(0, 23)
ax.set_xticks(x)
ax.set_xticklabels(xlabels, fontsize=TEXT_SIZE_XYAXIS)
ax.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)
ax.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
# ax.legend(loc='upper left', frameon=False, ncol=1, fontsize=TEXT_SIZE_LEGEND)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
# Make axis lines thicker
ax.spines['left'].set_linewidth(1)
ax.spines['bottom'].set_linewidth(1)

plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'threads-global')
plt.close(fig)

