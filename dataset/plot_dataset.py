#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

def read_data_file(file_path):
    """Read data from txt file, return labels and values"""
    labels = []
    values = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    # Handle labels that might have spaces (like "scaling factor")
                    label = ' '.join(parts[:-1])
                    value = int(parts[-1])
                    labels.append(label)
                    values.append(value)
    return labels, values

def get_nice_yticks(max_value):
    """Calculate y-axis ticks that are multiples of 5, 10, or 20"""
    # Calculate desired upper limit
    desired_upper = max_value * 1.2
    
    # Determine appropriate step size based on max value
    if max_value <= 25:
        step = 5
    elif max_value <= 60:
        step = 10
    elif max_value <= 100:
        step = 20
    else:
        # For values > 100, use larger step (40, which is 20*2)
        step = 40
    
    # Round upper limit to next multiple of step
    upper_limit = ((int(desired_upper) // step) + 1) * step
    
    # Ensure we have at least 4-5 ticks, but not too many (max 8 ticks)
    num_ticks = upper_limit // step + 1
    if num_ticks < 4:
        # If too few ticks, try smaller step
        if step == 40:
            step = 20
        elif step == 20:
            step = 10
        elif step == 10:
            step = 5
        upper_limit = ((int(desired_upper) // step) + 1) * step
    elif num_ticks > 8:
        # If too many ticks, try larger step
        if step == 20:
            step = 40
        elif step == 10:
            step = 20
        elif step == 5:
            step = 10
        upper_limit = ((int(desired_upper) // step) + 1) * step
    
    # Generate ticks
    ticks = np.arange(0, upper_limit + step, step)
    return ticks, upper_limit

def plot_combined():
    """Plot all three datasets in subplots"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Read data from all three files
    cat1_labels, cat1_values = read_data_file(os.path.join(script_dir, 'category1.txt'))
    cat2_labels, cat2_values = read_data_file(os.path.join(script_dir, 'category2.txt'))
    sub_labels, sub_values = read_data_file(os.path.join(script_dir, 'subsystem.txt'))
    
    # Create figure with subplots - use GridSpec for flexible layout
    from matplotlib.gridspec import GridSpec
    fig = plt.figure(figsize=(16, 8))
    # Use height_ratios to make top row shorter
    # Adjust ratio to make bottom plot also shorter
    # Reduce hspace to decrease spacing between top and bottom plots
    gs = GridSpec(2, 2, figure=fig, hspace=0.25, wspace=0.3, height_ratios=[1, 1.1])
    
    # Plot category1 (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    x1 = np.arange(len(cat1_labels))
    bars1 = ax1.bar(x1, cat1_values, color=plot_common.colors[1], edgecolor='black', linewidth=1, zorder=2)
    ax1.set_xticks(x1)
    ax1.set_xticklabels(cat1_labels, rotation=0, ha='center')
    ax1.tick_params(axis='x', length=0)
    ax1.set_ylabel('Count')
    # Set y-axis ticks to show more numbers (multiples of 5, 10, or 20)
    max_val1 = max(cat1_values)
    yticks1, ymax1 = get_nice_yticks(max_val1)
    ax1.set_ylim(0, ymax1)
    ax1.set_yticks(yticks1)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_linewidth(1)
    ax1.spines['bottom'].set_linewidth(1)
    ax1.tick_params(axis='x', length=0, width=0)
    ax1.tick_params(axis='y', length=8, width=2)
    # Add value labels on bars
    for bar, value in zip(bars1, cat1_values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom')
    
    # Plot category2 (top right)
    ax2 = fig.add_subplot(gs[0, 1])
    x2 = np.arange(len(cat2_labels))
    bars2 = ax2.bar(x2, cat2_values, color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(cat2_labels, rotation=0, ha='center')
    ax2.tick_params(axis='x', length=0)
    ax2.set_ylabel('Count')
    # Set y-axis ticks to show more numbers (multiples of 5, 10, or 20)
    max_val2 = max(cat2_values)
    yticks2, ymax2 = get_nice_yticks(max_val2)
    ax2.set_ylim(0, ymax2)
    ax2.set_yticks(yticks2)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_linewidth(2.5)
    ax2.spines['bottom'].set_linewidth(2.5)
    ax2.tick_params(axis='x', length=0, width=0)
    ax2.tick_params(axis='y', length=8, width=2)
    # Add value labels on bars
    for bar, value in zip(bars2, cat2_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom')
    
    # Plot subsystem (bottom, spanning both columns)
    ax3 = fig.add_subplot(gs[1, :])
    x3 = np.arange(len(sub_labels))
    bars3 = ax3.bar(x3, sub_values, color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
    ax3.set_xticks(x3)
    ax3.set_xticklabels(sub_labels, rotation=0, ha='center')
    ax3.tick_params(axis='x', length=0)
    ax3.set_ylabel('Count')
    # Set y-axis ticks to show more numbers (multiples of 5, 10, or 20)
    max_val3 = max(sub_values)
    yticks3, ymax3 = get_nice_yticks(max_val3)
    ax3.set_ylim(0, ymax3)
    ax3.set_yticks(yticks3)
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['left'].set_linewidth(2.5)
    ax3.spines['bottom'].set_linewidth(2.5)
    ax3.tick_params(axis='x', length=0, width=0)
    ax3.tick_params(axis='y', length=8, width=2)
    # Add value labels on bars
    for bar, value in zip(bars3, sub_values):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom')
    
    fig.tight_layout()
    plot_common.save_fig(script_dir, 'dataset_distribution')
    plt.close(fig)

def plot_two_figures():
    """Plot categories in one figure and subsystem in another"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Read data from all three files
    cat1_labels, cat1_values = read_data_file(os.path.join(script_dir, 'category1.txt'))
    cat2_labels, cat2_values = read_data_file(os.path.join(script_dir, 'category2.txt'))
    sub_labels, sub_values = read_data_file(os.path.join(script_dir, 'subsystem.txt'))
    
    # Figure 1: Categories (side by side)
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot category1
    x1 = np.arange(len(cat1_labels))
    bars1 = ax1.bar(x1, cat1_values, color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
    ax1.set_xticks(x1)
    ax1.set_xticklabels(cat1_labels, rotation=0, ha='center')
    ax1.tick_params(axis='x', length=0)
    ax1.set_ylabel('Count')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_linewidth(1)
    ax1.spines['bottom'].set_linewidth(1)
    ax1.tick_params(axis='x', length=0, width=0)
    ax1.tick_params(axis='y', length=8, width=2)
    for bar, value in zip(bars1, cat1_values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom')
    
    # Plot category2
    x2 = np.arange(len(cat2_labels))
    bars2 = ax2.bar(x2, cat2_values, color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(cat2_labels, rotation=0, ha='center')
    ax2.tick_params(axis='x', length=0)
    ax2.set_ylabel('Count')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_linewidth(2.5)
    ax2.spines['bottom'].set_linewidth(2.5)
    ax2.tick_params(axis='x', length=0, width=0)
    ax2.tick_params(axis='y', length=8, width=2)
    for bar, value in zip(bars2, cat2_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    # plot_common.save_fig(script_dir, 'categories_distribution')
    plt.close(fig1)
    
    # Figure 2: Subsystem
    fig2, ax3 = plt.subplots(1, 1, figsize=(12, 6))
    x3 = np.arange(len(sub_labels))
    bars3 = ax3.bar(x3, sub_values, color=plot_common.colors[1], edgecolor='black', linewidth=1, zorder=2)
    ax3.set_xticks(x3)
    ax3.set_xticklabels(sub_labels, rotation=0, ha='center')
    ax3.tick_params(axis='x', length=0)
    ax3.set_ylabel('Count')
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['left'].set_linewidth(2.5)
    ax3.spines['bottom'].set_linewidth(2.5)
    ax3.tick_params(axis='x', length=0, width=0)
    ax3.tick_params(axis='y', length=8, width=2)
    for bar, value in zip(bars3, sub_values):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    # plot_common.save_fig(script_dir, 'subsystem_distribution')
    plt.close(fig2)

if __name__ == "__main__":
    print("Generating combined figure (all in one)...")
    plot_combined()
    
    print("\nGenerating two separate figures...")
    plot_two_figures()
    
    print("\nDone! Check the generated PDF files.")

