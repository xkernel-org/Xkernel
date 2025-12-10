#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import seaborn as sns

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Use mako color palette
palette = sns.color_palette("mako")

# Unified font sizes
TEXT_SIZE_XYLABEL = 20
TEXT_SIZE_XYAXIS = 18
TEXT_SIZE_TEXT = 18
TEXT_SIZE_LEGEND = 18

"""
Caveats:

1. SS now has a total number of 135 instead of 140. Because:
    - The duplicate BFQ_RATE_MIN_SAMPLES is counted only once (-1)
    - MLD_MAX_QUEUE, MAX_MADVISE_GUARD_RETRIES, MAX_VMAP_RETRIES, TCP_DELACK_MAX
      produced huge IR diff and we gave them up (-4)
2. SS is characterized using one of the following ways:
   a. disjoint IR spans. Recall that we calculate SS size by adding (1) top level
      spans + (2) lower level full functions. Here the number is number of top
      level spans.
   b. disjoint assembly spans
   c. Number of disjoint CSes - (number of IR starting points - clustered dataflow results)
"""

def get_ss_number_dist():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # TODO change this to make CS and SS consistent
    bars = [
        { 'label': '1', 'condition': lambda x: x == 1, 'count': 0 },
        { 'label': '2', 'condition': lambda x: x == 2, 'count': 0 },
        { 'label': '3', 'condition': lambda x: x == 3, 'count': 0 },
        { 'label': '4', 'condition': lambda x: x == 4, 'count': 0 },
        { 'label': '5-10', 'condition': lambda x: x >= 5 and x <= 10, 'count': 0 },
        { 'label': '> 10', 'condition': lambda x: x > 10, 'count': 0 },
    ]

    # TODO choose what we want to present in terms of SS 
    input_data = 'disjoint_sses.txt'
    # input_data = 'disjoint_sses_asm.txt'

    with open(os.path.join(script_dir, input_data), 'r') as f:
        lines = f.readlines()
        for line in lines:
            size = int(line.strip())
            for bar in bars:
                if bar['condition'](size):
                    bar['count'] += 1

    with open(os.path.join(script_dir, 'ss_number_dist.txt'), 'w') as f:
        f.write("Number of SS, Count\n")
        for bar in bars:
            f.write(f"{bar['label']}, {bar['count']}\n")

def read_ss_number_data(file_path):
    """Read SS number distribution data from CSV file"""
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
    
    fig, ax = plt.subplots(figsize=(8, 3))
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=palette[2], zorder=2)
    
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=TEXT_SIZE_XYAXIS)
    ax.tick_params(axis='x', length=6, width=1, direction='out', labelsize=TEXT_SIZE_XYAXIS)
    ax.set_xlabel('# of CS', fontsize=TEXT_SIZE_XYLABEL)
    ax.set_ylabel('Count', fontsize=TEXT_SIZE_XYLABEL)
    
    max_val = max(values)
    yticks, ymax = get_nice_yticks(max_val)
    ax.set_ylim(0, ymax)
    ax.set_yticks(yticks)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)
    ax.tick_params(axis='y', length=8, width=2, labelsize=TEXT_SIZE_XYAXIS)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT)
    
    plt.tight_layout()
    plot_common.save_fig(script_dir, 'cs_number_dist')
    plt.close(fig)

def plot_cs_and_ss_number():
    """Plot CS and SS number distribution as grouped bar chart"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cs_data_file = os.path.join(script_dir, 'cs_number_dist.txt')
    ss_data_file = os.path.join(script_dir, 'ss_number_dist.txt')

    cs_labels, cs_values = read_cs_number_data(cs_data_file)
    ss_labels, ss_values = read_ss_number_data(ss_data_file)

    x = np.arange(len(ss_labels))  # label locations
    width = 0.36  # width of each bar

    fig, ax = plt.subplots(figsize=(8, 3))
    cs_bars = ax.bar(x - width/2, cs_values, width, label='CS', color=palette[3], zorder=2)
    ss_bars = ax.bar(x + width/2, ss_values, width, label='SS', color=palette[2], zorder=2)

    ax.set_xticks(x)
    ax.set_xticklabels(ss_labels, rotation=0, ha='center', fontsize=TEXT_SIZE_XYAXIS)
    ax.set_xlabel('# of CS or SS', fontsize=TEXT_SIZE_XYLABEL)
    ax.set_ylabel('Count', fontsize=TEXT_SIZE_XYLABEL)
    ax.legend(frameon=False, fontsize=TEXT_SIZE_LEGEND)
    ax.tick_params(axis='x', length=6, width=1, direction='out', labelsize=TEXT_SIZE_XYAXIS)

    max_val = max(max(cs_values), max(ss_values))
    yticks, ymax = get_nice_yticks(max_val)
    ax.set_ylim(0, ymax)
    ax.set_yticks(yticks)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)
    ax.tick_params(axis='y', length=8, width=2, labelsize=TEXT_SIZE_XYAXIS)

    # Add value labels on bars for both CS and SS
    for bar, value in zip(cs_bars, cs_values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}', ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT)

    for bar, value in zip(ss_bars, ss_values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}', ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT)

    plt.tight_layout()
    plot_common.save_fig(script_dir, 'cs_number_dist')
    plt.close(fig)

if __name__ == "__main__":
    get_ss_number_dist()

    # plot_cs_number()
    plot_cs_and_ss_number()

    print("Done!")
