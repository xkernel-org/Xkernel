#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

def read_cs_number_data(file_path):
    """Read CS number distribution data from CSV file"""
    labels = []
    values = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        # Skip header line
        for line in lines[1:]:
            line = line.strip()
            if line:
                parts = line.split(',')
                if len(parts) >= 2:
                    label = parts[0].strip()
                    value = int(parts[1].strip())
                    labels.append(label)
                    values.append(value)
    return labels, values

def get_nice_yticks(max_value):
    """Calculate y-axis ticks that are multiples of 5, 10, or 20"""
    desired_upper = max_value * 1.2
    
    if max_value <= 25:
        step = 5
    elif max_value <= 60:
        step = 10
    elif max_value <= 100:
        step = 20
    else:
        step = 40
    
    upper_limit = ((int(desired_upper) // step) + 1) * step
    
    num_ticks = upper_limit // step + 1
    if num_ticks < 4:
        if step == 40:
            step = 20
        elif step == 20:
            step = 10
        elif step == 10:
            step = 5
        upper_limit = ((int(desired_upper) // step) + 1) * step
    elif num_ticks > 8:
        if step == 20:
            step = 40
        elif step == 10:
            step = 20
        elif step == 5:
            step = 10
        upper_limit = ((int(desired_upper) // step) + 1) * step
    
    ticks = np.arange(0, upper_limit + step, step)
    return ticks, upper_limit

def plot_cs_number():
    """Plot CS number distribution as bar chart"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(script_dir, 'cs_number_dist.txt')
    
    labels, values = read_cs_number_data(data_file)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
    
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, ha='center')
    ax.tick_params(axis='x', length=0)
    ax.set_xlabel('# of CS')
    ax.set_ylabel('Count')
    
    max_val = max(values)
    yticks, ymax = get_nice_yticks(max_val)
    ax.set_ylim(0, ymax)
    ax.set_yticks(yticks)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)
    ax.tick_params(axis='x', length=6, width=2)
    ax.tick_params(axis='y', length=8, width=2)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    plot_common.save_fig(script_dir, 'cs_number_dist')
    plt.close(fig)

if __name__ == "__main__":
    plot_cs_number()
    print("Done!")

