#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import seaborn as sns
from matplotlib.textpath import TextPath
from matplotlib import font_manager

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Use mako color palette
palette = sns.color_palette("mako")

# Unified font sizes
TEXT_SIZE_XYLABEL = 20
TEXT_SIZE_XYAXIS = 18
TEXT_SIZE_TEXT = 18

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

def process_subsystem_data(sub_labels, sub_values):
    """Process subsystem data: merge block, io, fs into storage with stacked components"""
    storage_labels = ['block', 'io', 'fs']
    new_sub_data = {}  # {label: value or {stacked components}}
    
    for label, value in zip(sub_labels, sub_values):
        if label in storage_labels:
            if 'storage' not in new_sub_data:
                new_sub_data['storage'] = {}
            new_sub_data['storage'][label] = value
        else:
            new_sub_data[label] = value
    
    # Create labels and values for plotting
    plot_labels = []
    plot_values = []  # For non-stacked bars
    storage_stack = []  # [block, io, fs] values for stacked bar
    
    # Determine order: put storage first, then others
    if 'storage' in new_sub_data:
        plot_labels.append('storage')
        storage_stack = [
            new_sub_data['storage'].get('block', 0),
            new_sub_data['storage'].get('io', 0),
            new_sub_data['storage'].get('fs', 0)
        ]
        plot_values.append(None)  # Placeholder for stacked bar
    
    # Add other labels
    for label, value in zip(sub_labels, sub_values):
        if label not in storage_labels:
            plot_labels.append(label)
            plot_values.append(value)
    
    return plot_labels, plot_values, storage_stack

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
    
    # Create figure with subplots - three plots in one row
    # Control spacing between subplots: wspace controls horizontal spacing (as fraction of subplot width)
    subplot_wspace = 0.08  # Adjust this value to control spacing between subplots (smaller = closer)
    # Control width ratios: 30%, 30%, 40%
    width_ratios = [3.8, 3, 3.2]  # Swapped first and third
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 2.2), 
                                        gridspec_kw={'wspace': subplot_wspace, 'width_ratios': width_ratios})
    
    # Compress x positions and bar width
    x_spacing = 0.4  # Reduce spacing between bars (smaller = closer)
    bar_width = 0.3  # Reduce bar width (smaller = narrower)
    
    # Plot subsystem (left) - moved from third position
    # Merge block, io, fs into storage with stacked bars
    
    # Process subsystem data
    plot_labels, plot_values, storage_stack = process_subsystem_data(sub_labels, sub_values)
    
    x1 = np.arange(len(plot_labels)) * x_spacing
    
    # Draw stacked bar for storage
    storage_idx = None
    storage_x_pos = None
    if 'storage' in plot_labels:
        storage_idx = plot_labels.index('storage')
        storage_x_pos = x1[storage_idx]  # Get actual x position
        bottom = 0
        storage_color = palette[2]  # Use same color for all components
        storage_component_labels = ['block', 'io', 'fs']
        for i, (comp_label, comp_value) in enumerate(zip(storage_component_labels, storage_stack)):
            if comp_value > 0:
                ax1.bar(storage_x_pos, comp_value, width=bar_width, bottom=bottom, 
                       color=storage_color, edgecolor='black', linewidth=1, zorder=2)
                # Add label on each stacked component
                mid_y = bottom + comp_value / 2
                # ax1.text(storage_x_pos, mid_y, f'{comp_label}:{comp_value}',
                ax1.text(storage_x_pos, mid_y, f'{comp_label}',
                        ha='center', va='center', fontsize=TEXT_SIZE_TEXT - 5, fontweight='bold',
                        color='white' if comp_value > 5 else 'black')
                bottom += comp_value
    
    # Draw regular bars for others
    for i, (label, value) in enumerate(zip(plot_labels, plot_values)):
        if label != 'storage' and value is not None:
            ax1.bar(x1[i], value, width=bar_width, color=palette[2], zorder=2)
    
    ax1.set_xticks(x1)
    ax1.set_xticklabels(plot_labels, rotation=0, ha='center', fontsize=TEXT_SIZE_XYAXIS)
    ax1.set_ylabel('Count', fontsize=TEXT_SIZE_XYLABEL)
    
    # Calculate storage_total for labels (still needed for text labels)
    storage_total = sum(storage_stack)
    
    # Set unified y-axis ticks
    yticks_unified = [0, 25, 50, 75, 100, 125]
    ax1.set_ylim(0, 126)
    ax1.set_yticks(yticks_unified)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_linewidth(1)
    ax1.spines['bottom'].set_linewidth(1)
    ax1.tick_params(axis='x', length=6, width=1, direction='out', labelsize=TEXT_SIZE_XYAXIS)
    ax1.tick_params(axis='y', length=8, width=2, labelsize=TEXT_SIZE_XYAXIS)
    
    # Add value labels on bars
    # For storage stacked bar, show total on top
    if storage_total > 0 and storage_idx is not None and storage_x_pos is not None:
        ax1.text(storage_x_pos, storage_total, f'{storage_total}',
                ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT, fontweight='bold')
    
    # For other bars
    for i, (label, value) in enumerate(zip(plot_labels, plot_values)):
        if label != 'storage' and value is not None:
            ax1.text(x1[i], value, f'{value}',
                    ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT)
    
    # Plot category2 (middle)
    x2 = np.arange(len(cat2_labels)) * x_spacing
    bars2 = ax2.bar(x2, cat2_values, width=bar_width, color=palette[3], zorder=2)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(cat2_labels, rotation=0, ha='center', fontsize=TEXT_SIZE_XYAXIS)
    ax2.set_ylabel('')
    # Set unified y-axis ticks
    ax2.set_ylim(0, 126)
    ax2.set_yticks(yticks_unified)
    ax2.set_yticklabels([])  # Hide y-axis tick labels
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_linewidth(1)
    ax2.spines['bottom'].set_linewidth(1)
    ax2.tick_params(axis='x', length=6, width=1, direction='out', labelsize=TEXT_SIZE_XYAXIS)
    ax2.tick_params(axis='y', length=8, width=2, labelsize=TEXT_SIZE_XYAXIS)
    # Add value labels on bars
    for bar, value in zip(bars2, cat2_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT)
    
    # Plot category1 (right) - moved from first position
    x3 = np.arange(len(cat1_labels)) * x_spacing
    bars3 = ax3.bar(x3, cat1_values, width=bar_width, color=palette[4], zorder=2)
    ax3.set_xticks(x3)
    ax3.set_xticklabels(cat1_labels, rotation=0, ha='center', fontsize=TEXT_SIZE_XYAXIS)
    ax3.set_ylabel('')
    # Set unified y-axis ticks
    ax3.set_ylim(0, 126)
    ax3.set_yticks(yticks_unified)
    ax3.set_yticklabels([])  # Hide y-axis tick labels
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['left'].set_linewidth(1)
    ax3.spines['bottom'].set_linewidth(1)
    ax3.tick_params(axis='x', length=6, width=1, direction='out', labelsize=TEXT_SIZE_XYAXIS)
    ax3.tick_params(axis='y', length=8, width=2, labelsize=TEXT_SIZE_XYAXIS)
    # Add value labels on bars
    for bar, value in zip(bars3, cat1_values):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT)
    
    fig.tight_layout()
    
    # Add subplot labels in USENIX style (Times New Roman font)
    SUBFIG_SPACE = 0.2
    SUBFIG_TEXT_SIZE = 26
    
    # Label for first subplot (a) Subsystem - swapped from third
    ax1_bbox = ax1.get_position()
    label_x1 = ax1_bbox.x0 + ax1_bbox.width / 2  # Center of ax1
    label_x1 -= 0.1
    label_y1 = ax1_bbox.y0 - SUBFIG_SPACE
    
    # Measure widths using TextPath
    prop = font_manager.FontProperties(family='Times New Roman', size=SUBFIG_TEXT_SIZE)
    path_a_full = TextPath((0, 0), '(a) Subsystem', prop=prop, size=SUBFIG_TEXT_SIZE)
    path_a_label = TextPath((0, 0), '(a) ', prop=prop, size=SUBFIG_TEXT_SIZE)
    bbox_a_full = path_a_full.get_extents()
    bbox_a_label = path_a_label.get_extents()
    total_width_a = bbox_a_full.width / fig.dpi / fig.get_figwidth()
    width_a_label = bbox_a_label.width / fig.dpi / fig.get_figwidth()
    
    # Draw "(a) " without bold
    fig.text(label_x1 - total_width_a / 2 - 0.03, label_y1, '(a) ', 
             ha='left', va='top', fontsize=SUBFIG_TEXT_SIZE, 
             family='Times New Roman', weight='normal')
    # Draw "Subsystem" with bold
    fig.text(label_x1 - total_width_a / 2 + width_a_label + 0.02, label_y1 - 0.005, 'Subsystem', 
             ha='left', va='top', fontsize=SUBFIG_TEXT_SIZE, 
             family='Times New Roman', weight='normal')
    
    # Label for second subplot (b) Source form
    ax2_bbox = ax2.get_position()
    label_x2 = ax2_bbox.x0 + ax2_bbox.width / 2  # Center of ax2
    label_x2 -= 0.12
    label_y2 = ax2_bbox.y0 - SUBFIG_SPACE
    
    path_b_full = TextPath((0, 0), '(b) Source form', prop=prop, size=SUBFIG_TEXT_SIZE)
    path_b_label = TextPath((0, 0), '(b) ', prop=prop, size=SUBFIG_TEXT_SIZE)
    bbox_b_full = path_b_full.get_extents()
    bbox_b_label = path_b_label.get_extents()
    total_width_b = bbox_b_full.width / fig.dpi / fig.get_figwidth()
    width_b_label = bbox_b_label.width / fig.dpi / fig.get_figwidth()
    
    # Draw "(b) " without bold
    fig.text(label_x2 - total_width_b / 2, label_y2, '(b) ', 
             ha='left', va='top', fontsize=SUBFIG_TEXT_SIZE, 
             family='Times New Roman', weight='normal')
    # Draw "Source form" with bold - move down a bit
    fig.text(label_x2 - total_width_b / 2 + width_b_label+ 0.05, label_y2 - 0.01, 'Source form', 
             ha='left', va='top', fontsize=SUBFIG_TEXT_SIZE, 
             family='Times New Roman', weight='normal')
    
    # Label for third subplot (c) Semantics - swapped from first
    ax3_bbox = ax3.get_position()
    label_x3 = ax3_bbox.x0 + ax3_bbox.width / 2  # Center of ax3
    label_x3 -= 0.13
    label_y3 = ax3_bbox.y0 - SUBFIG_SPACE
    
    path_c_full = TextPath((0, 0), '(c) Semantics', prop=prop, size=SUBFIG_TEXT_SIZE)
    path_c_label = TextPath((0, 0), '(c) ', prop=prop, size=SUBFIG_TEXT_SIZE)
    bbox_c_full = path_c_full.get_extents()
    bbox_c_label = path_c_label.get_extents()
    total_width_c = bbox_c_full.width / fig.dpi / fig.get_figwidth()
    width_c_label = bbox_c_label.width / fig.dpi / fig.get_figwidth()
    
    # Draw "(c) " without bold
    fig.text(label_x3 - total_width_c / 2 + 0.03, label_y3, '(c) ', 
             ha='left', va='top', fontsize=SUBFIG_TEXT_SIZE, 
             family='Times New Roman', weight='normal')
    # Draw "Semantics" with bold - move down a bit
    fig.text(label_x3 - total_width_c / 2 + width_c_label+ 0.08, label_y3 - 0.015, 'Semantics', 
             ha='left', va='top', fontsize=SUBFIG_TEXT_SIZE, 
             family='Times New Roman', weight='normal')
    
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
    bars1 = ax1.bar(x1, cat1_values, color=palette[2], zorder=2)
    ax1.set_xticks(x1)
    ax1.set_xticklabels(cat1_labels, rotation=0, ha='center', fontsize=TEXT_SIZE_XYAXIS)
    ax1.set_ylabel('Count', fontsize=TEXT_SIZE_XYLABEL)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_linewidth(1)
    ax1.spines['bottom'].set_linewidth(1)
    ax1.tick_params(axis='x', length=6, width=1, direction='out', labelsize=TEXT_SIZE_XYAXIS)
    ax1.tick_params(axis='y', length=8, width=2, labelsize=TEXT_SIZE_XYAXIS)
    for bar, value in zip(bars1, cat1_values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT)
    
    # Plot category2
    x2 = np.arange(len(cat2_labels))
    bars2 = ax2.bar(x2, cat2_values, color=palette[4], zorder=2)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(cat2_labels, rotation=0, ha='center', fontsize=TEXT_SIZE_XYAXIS)
    ax2.set_ylabel('Count', fontsize=TEXT_SIZE_XYLABEL)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_linewidth(2.5)
    ax2.spines['bottom'].set_linewidth(2.5)
    ax2.tick_params(axis='x', length=6, width=1, direction='out', labelsize=TEXT_SIZE_XYAXIS)
    ax2.tick_params(axis='y', length=8, width=2, labelsize=TEXT_SIZE_XYAXIS)
    for bar, value in zip(bars2, cat2_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT)
    
    plt.tight_layout()
    # plot_common.save_fig(script_dir, 'categories_distribution')
    plt.close(fig1)
    
    # Figure 2: Subsystem
    fig2, ax3 = plt.subplots(1, 1, figsize=(12, 6))
    
    # Process subsystem data
    plot_labels, plot_values, storage_stack = process_subsystem_data(sub_labels, sub_values)
    
    x3 = np.arange(len(plot_labels))
    
    # Draw stacked bar for storage
    storage_idx = None
    if 'storage' in plot_labels:
        storage_idx = plot_labels.index('storage')
        bottom = 0
        storage_color = palette[2]  # Use same color for all components
        storage_component_labels = ['block', 'io', 'fs']
        for i, (comp_label, comp_value) in enumerate(zip(storage_component_labels, storage_stack)):
            if comp_value > 0:
                ax3.bar(storage_idx, comp_value, bottom=bottom, 
                       color=storage_color, edgecolor='black', linewidth=1, zorder=2)
                # Add label on each stacked component
                mid_y = bottom + comp_value / 2
                ax3.text(storage_idx, mid_y, f'{comp_label}\n{comp_value}',
                        ha='center', va='center', fontsize=TEXT_SIZE_TEXT, fontweight='bold',
                        color='white' if comp_value > 5 else 'black')
                bottom += comp_value
    
    # Draw regular bars for others
    for i, (label, value) in enumerate(zip(plot_labels, plot_values)):
        if label != 'storage' and value is not None:
            ax3.bar(i, value, color=palette[1], zorder=2)
    
    ax3.set_xticks(x3)
    ax3.set_xticklabels(plot_labels, rotation=0, ha='center', fontsize=TEXT_SIZE_XYAXIS)
    ax3.set_ylabel('Count', fontsize=TEXT_SIZE_XYLABEL)
    
    # Calculate max value for y-axis
    storage_total = sum(storage_stack)
    other_max = max([v for v in plot_values if v is not None]) if any(v is not None for v in plot_values) else 0
    max_val3 = max(storage_total, other_max)
    yticks3, ymax3 = get_nice_yticks(max_val3)
    ax3.set_ylim(0, ymax3)
    ax3.set_yticks(yticks3)
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['left'].set_linewidth(2.5)
    ax3.spines['bottom'].set_linewidth(2.5)
    ax3.tick_params(axis='x', length=6, width=1, direction='out', labelsize=TEXT_SIZE_XYAXIS)
    ax3.tick_params(axis='y', length=8, width=2, labelsize=TEXT_SIZE_XYAXIS)
    
    # Add value labels on bars
    # For storage stacked bar, show total on top
    if storage_total > 0 and storage_idx is not None:
        ax3.text(storage_idx, storage_total, f'{storage_total}',
                ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT, fontweight='bold')
    
    # For other bars
    for i, (label, value) in enumerate(zip(plot_labels, plot_values)):
        if label != 'storage' and value is not None:
            ax3.text(i, value, f'{value}',
                    ha='center', va='bottom', fontsize=TEXT_SIZE_TEXT)
    
    plt.tight_layout()
    # plot_common.save_fig(script_dir, 'subsystem_distribution')
    plt.close(fig2)

if __name__ == "__main__":
    print("Generating combined figure (all in one)...")
    plot_combined()
    
    print("\nGenerating two separate figures...")
    plot_two_figures()
    
    print("\nDone! Check the generated PDF files.")

