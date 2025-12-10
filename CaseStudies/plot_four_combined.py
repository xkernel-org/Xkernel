#!/usr/bin/env python3
# Combined plot for migr_lat, migr_tlb, softirq, and shrink
import os
import re
import glob
import csv
import numpy as np
import matplotlib.pyplot as plt
from math import ceil, log10, floor
from matplotlib.ticker import MaxNLocator, LogLocator
from matplotlib.patches import Rectangle
import sys
import seaborn as sns

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Unified color palette for all three subplots
palette = sns.color_palette("mako")

HEIGHT = 3

# Text size for subplots
TEXT_SIZE_1 = 18  # First subplot (cs1)
TEXT_SIZE_2 = 18  # Second subplot (cs2)
TEXT_SIZE_3 = 18  # Third subplot (cs3)

# Unified text sizes
TEXT_SIZE_XYLABEL = 18
TEXT_SIZE_XYAXIS = 18
TEXT_SIZE_LEGEND = 17

# Tick parameters
TICK_LENGTH_X = 5
TICK_WIDTH_X = 1

SEPARATOR = '************************************'

# ==========================================
# Helper functions for migr_lat
# ==========================================
def _extract_number_from_filename(fname: str) -> int:
    m = re.search(r'(\d+)', os.path.basename(fname))
    return int(m.group(1)) if m else 10**9

def _clean_float(s: str) -> float:
    return float(s.replace(',', ''))

def to_int(s: str) -> int:
    return int(s.replace(',', ''))

def _pick_probe_block(content: str) -> str:
    parts = content.split(SEPARATOR)
    if len(parts) >= 2:
        cand = parts[-1]
        if re.search(r'\bP(?:50|90|95|99)\s*,', cand):
            return cand

    last_probe = None
    for m in re.finditer(r'(?i)Probe\s+La?ten(?:cy|cy)', content):
        last_probe = m
    if last_probe:
        return content[last_probe.start():]

    return content  

def parse_latency_data(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw = f.read()

        block = _pick_probe_block(raw)

        p50 = re.search(r'\bP50\s*,\s*([\d,]+(?:\.\d+)?)', block)
        p90 = re.search(r'\bP90\s*,\s*([\d,]+(?:\.\d+)?)', block)
        p95 = re.search(r'\bP95\s*,\s*([\d,]+(?:\.\d+)?)', block)
        p99 = re.search(r'\bP99\s*,\s*([\d,]+(?:\.\d+)?)', block)

        if not all([p50, p90, p95, p99]):
            print(f"[warn] Missing Pxx in: {filepath}")
            return None

        return {
            'p50': _clean_float(p50.group(1)),
            'p90': _clean_float(p90.group(1)),
            'p95': _clean_float(p95.group(1)),
            'p99': _clean_float(p99.group(1)),
        }
    except Exception as e:
        print(f"[error] {filepath}: {e}")
        return None

# ==========================================
# Helper functions for migr_tlb
# ==========================================
PAT_REASON_1 = re.compile(r'@tlb_reason_cnt\[1\]:\s*([\d,]+)')
PAT_REASON_4 = re.compile(r'@tlb_reason_cnt\[4\]:\s*([\d,]+)')

def parse_tlb_file(path: str):
    """Return (batch_size, reason1, reason4) or None on failure."""
    base = os.path.splitext(os.path.basename(path))[0]
    try:
        batch_size = int(base)
    except ValueError:
        return None

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        return None

    m1 = PAT_REASON_1.search(content)
    m4 = PAT_REASON_4.search(content)
    if not (m1 and m4):
        return None

    try:
        r1 = to_int(m1.group(1))
        r4 = to_int(m4.group(1))
    except Exception:
        return None

    return (batch_size, r1, r4)

# ==========================================
# Helper functions for shrink
# ==========================================
def extract_data_from_file(file_path):
    dt_us = []
    cpu_usage = []

    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if "iter" in line:
                parts = line.split()
                dt_us.append(int(parts[2].split('=')[1]))
            elif "elapsed" in line:
                time_info = line.split()
                cpu_usage.append(float(time_info[3].replace('CPU', '').replace('%', '').strip()))

    return dt_us, cpu_usage

def calculate_percentiles(data):
    p50 = np.percentile(data, 50)
    p90 = np.percentile(data, 90)
    p99 = np.percentile(data, 99)
    return p50, p90, p99

def process_shrink_files(directory):
    all_dt_us = []
    all_cpu_usage = []
    labels = []
    
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            file_name = os.path.basename(file_path).split('.')[0]
            labels.append(file_name)
            
            dt_us, cpu_usage = extract_data_from_file(file_path)
            p50, p90, p99 = calculate_percentiles(dt_us)
            
            all_dt_us.append((p50, p90, p99))
            all_cpu_usage.append(np.mean(cpu_usage))

    # Sort by integer value of label
    sorted_labels = sorted(labels, key=lambda x: int(x))
    sorted_dt_us = [all_dt_us[labels.index(label)] for label in sorted_labels]
    sorted_cpu_usage = [all_cpu_usage[labels.index(label)] for label in sorted_labels]

    return sorted_dt_us, sorted_cpu_usage, sorted_labels

# ==========================================
# Plotting functions
# ==========================================
def _nice_step(max_val: float, goal_ticks: int = 6) -> float:
    if max_val <= 0:
        return 1.0
    exp = floor(log10(max_val))
    candidates = []
    for k in range(exp - 1, exp + 2):  
        base = 10 ** k
        candidates += [1 * base, 2 * base, 5 * base]
    for step in sorted(candidates):
        if max_val / step <= goal_ticks:
            return float(step)
    return float(max(candidates))

def create_four_combined_plot(migr_lat_dir, migr_tlb_dir, softirq_csv, shrink_dir, out_pdf):
    # Create figure with 4 subplots in one row
    # Order: softirq, shrink, migr_lat, migr_tlb
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(20, HEIGHT))
    
    # ==========================================
    # Plot 1: softirq
    # ==========================================
    if os.path.exists(softirq_csv):
        # Read CSV file
        max_restart = []
        worst_lat = []
        cpu_util = []
        with open(softirq_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['MAX_SOFTIRQ_TIME'] == '2ms':
                    max_restart.append(int(row['MAX_SOFTIRQ_RESTART']))
                    worst_lat.append(float(row['WorstLatUs']))
                    cpu_util.append(float(row['CpuUtilPct']))
        
        if max_restart:
            # Sort by MAX_SOFTIRQ_RESTART
            sorted_data = sorted(zip(max_restart, worst_lat, cpu_util))
            max_restart = [x[0] for x in sorted_data]
            worst_lat = [x[1] for x in sorted_data]
            cpu_util = [x[2] for x in sorted_data]

            color1 = palette[0]
            ax1.set_ylabel('Worst Latency (us)', color='black', fontsize=TEXT_SIZE_XYLABEL)
            ax1.plot(max_restart, worst_lat, 
                     marker=plot_common.markers[0], color=color1, linewidth=2, markersize=10, label='Worst Latency')
            ax1.tick_params(axis='y', labelcolor='black')
            ax1.tick_params(axis='x', labelcolor='black', length=TICK_LENGTH_X, width=TICK_WIDTH_X)
            ax1.set_ylim(bottom=0)
            ax1.set_yticks([250, 500, 700])
            ax1.set_xticks([1, 5, 10, 15, 20])
            ax1.set_xlabel('Value of Perf-Const', fontsize=TEXT_SIZE_XYLABEL)
            ax1.axvline(x=10, color='black', linestyle='--', linewidth=2, alpha=0.7)
            ax1.text(9.4, ax1.get_ylim()[1] * 0.95, 'Default Value', ha='center', va='top', color='black', fontsize=TEXT_SIZE_XYAXIS)

            ax1_twin = ax1.twinx()
            color2 = palette[2]
            ax1_twin.set_ylabel('CPU Usage (%)', color='black', fontsize=TEXT_SIZE_XYLABEL)
            ax1_twin.plot(max_restart, cpu_util, 
                         marker=plot_common.markers[2], color=color2, linewidth=2, markersize=10, label='CPU Usage')
            ax1_twin.tick_params(axis='y', labelcolor='black')
            ax1_twin.set_ylim(0, 100)

            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.spines['left'].set_color('black')
            ax1.spines['bottom'].set_color('black')
            ax1_twin.spines['top'].set_visible(False)
            ax1_twin.spines['left'].set_visible(False)
            ax1_twin.spines['right'].set_color('black')
            ax1_twin.spines['bottom'].set_color('black')

            # No legend for first plot

    # ==========================================
    # Plot 2: shrink
    # ==========================================
    if os.path.isdir(shrink_dir):
        all_dt_us, all_cpu_usage, labels = process_shrink_files(shrink_dir)
        
        if labels:
            p50 = [max(x[0], 1) for x in all_dt_us]
            p90 = [max(x[1], 1) for x in all_dt_us]
            p99 = [max(x[2], 1) for x in all_dt_us]

            width = 0.2
            x = np.arange(len(labels))

            ax2.bar(x - width, p50, label='P50', color=palette[2], width=width, zorder=2)
            ax2.bar(x, p90, label='P90', color=palette[3], width=width, zorder=2)
            ax2.bar(x + width, p99, label='P99', color=palette[1], width=width, zorder=2)

        ax2.set_ylabel('Delta Time (μs)', fontsize=TEXT_SIZE_XYLABEL)
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, fontsize=TEXT_SIZE_XYAXIS, rotation=45, ha='right')
        ax2.set_xlabel('Value of Perf-Const', fontsize=TEXT_SIZE_XYLABEL)
        ax2.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)
        ax2.set_yscale('log')
        ax2.yaxis.set_major_locator(LogLocator(base=10, numticks=20))
        ax2.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=100))
        ax2.tick_params(axis='y', which='major', length=8, width=2, labelsize=TEXT_SIZE_XYAXIS)
        ax2.tick_params(axis='y', which='minor', length=4, width=1.5)
        
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_linewidth(1)
        ax2.spines['bottom'].set_linewidth(1)

        ax2_twin = ax2.twinx()
        ax2_twin.plot(labels, all_cpu_usage, label='CPU Usage', color=palette[0], linewidth=2, marker=plot_common.markers[0], markersize=10, zorder=1)
        ax2_twin.set_ylabel('CPU Usage (%)', fontsize=TEXT_SIZE_XYLABEL)
        ax2_twin.set_ylim(0, 100)
        ax2_twin.tick_params(axis='y', length=10, width=2, labelsize=TEXT_SIZE_XYAXIS)
        
        handles1, labels1 = ax2.get_legend_handles_labels()
        handles2, labels2 = ax2_twin.get_legend_handles_labels()
        all_handles = handles1 + handles2
        all_labels = labels1 + labels2
        
        ax2.legend(all_handles, all_labels, loc='upper left', bbox_to_anchor=(0, 0.7), frameon=False, fontsize=TEXT_SIZE_LEGEND)
        
        ax2_twin.spines['top'].set_visible(False)
        ax2_twin.spines['right'].set_linewidth(1)

    # ==========================================
    # Plot 3: migr_lat (Latency)
    # ==========================================
    lat_txt_files = sorted(glob.glob(os.path.join(migr_lat_dir, '*.txt')), key=_extract_number_from_filename)
    if lat_txt_files:
        lat_labels = []
        p50_values, p90_values, p95_values, p99_values = [], [], [], []

        for path in lat_txt_files:
            stats = parse_latency_data(path)
            if not stats:
                continue
            m = re.search(r'(\d+)', os.path.basename(path))
            label = m.group(1) if m else os.path.basename(path)
            lat_labels.append(label)
            p50_values.append(stats['p50'])
            p90_values.append(stats['p90'])
            p95_values.append(stats['p95'])
            p99_values.append(stats['p99'])

        if lat_labels:
            # Convert to milliseconds
            p50 = np.asarray(p50_values, dtype=float) / 1000.0
            p90 = np.asarray(p90_values, dtype=float) / 1000.0
            p95 = np.asarray(p95_values, dtype=float) / 1000.0
            p99 = np.asarray(p99_values, dtype=float) / 1000.0

            x = np.arange(len(lat_labels))
            width_lat = 0.2

            r1 = ax3.bar(x - 1.5 * width_lat, p50, width_lat, label='P50', color=palette[2], zorder=2)
            r2 = ax3.bar(x - 0.5 * width_lat, p90, width_lat, label='P90', color=palette[3], zorder=2)
            r3 = ax3.bar(x + 0.5 * width_lat, p95, width_lat, label='P95', color=palette[1], zorder=2)
            r4 = ax3.bar(x + 1.5 * width_lat, p99, width_lat, label='P99', color=palette[0], zorder=2)

            ax3.set_ylabel('Latency (ms)', fontsize=TEXT_SIZE_XYLABEL)
            ax3.set_xticks(x)
            ax3.set_xticklabels(lat_labels, rotation=0, ha="center", fontsize=TEXT_SIZE_XYAXIS)
            ax3.set_xlabel('Value of Perf-Const', fontsize=TEXT_SIZE_XYLABEL)
            ax3.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)

            ymax_data = float(max(p50.max(initial=0), p90.max(initial=0), p95.max(initial=0), p99.max(initial=0)))
            goal_ticks = 6
            step = _nice_step(ymax_data, goal_ticks=goal_ticks)

            HEADROOM_FRAC = 0.06   
            y_top_aligned = ceil(ymax_data / step) * step
            y_top = y_top_aligned + HEADROOM_FRAC * ymax_data
            y_top = min(y_top, ymax_data * 1.08)

            ax3.set_ylim(0, y_top)

            ax3.yaxis.set_major_locator(MaxNLocator(nbins=goal_ticks, steps=[1, 2, 5, 10]))
            ax3.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)

            ax3.spines['top'].set_visible(False)
            ax3.spines['right'].set_visible(False)
            ax3.spines['left'].set_linewidth(1)
            ax3.spines['bottom'].set_linewidth(1)

            ax3.legend(loc='upper left', frameon=False, fontsize=TEXT_SIZE_LEGEND, ncol=2)

    # ==========================================
    # Plot 4: migr_tlb (TLB)
    # ==========================================
    tlb_paths = sorted(glob.glob(os.path.join(migr_tlb_dir, "*.txt")))
    if tlb_paths:
        tlb_rows = []
        for p in tlb_paths:
            res = parse_tlb_file(p)
            if res:
                tlb_rows.append((res[0], res[1], res[2]))
        
        if tlb_rows:
            tlb_rows.sort(key=lambda x: x[0])
            tlb_labels = [str(row[0]) for row in tlb_rows]
            reason1_values = [row[1] / 1000.0 for row in tlb_rows]
            reason4_values = [row[2] / 1000.0 for row in tlb_rows]

            x = np.arange(len(tlb_labels))
            width = 0.35

            rects1 = ax4.bar(x - width/2, reason1_values, width, label='CPU TLB Shootdown',
                            color=palette[2], zorder=2)
            rects2 = ax4.bar(x + width/2, reason4_values, width, label='Remote IPI Send',
                            color=palette[3], zorder=2)

            ax4.set_ylabel('Count (K)', fontsize=TEXT_SIZE_XYLABEL)
            ax4.set_xticks(x)
            ax4.set_xticklabels(tlb_labels, fontsize=TEXT_SIZE_XYAXIS)
            ax4.set_xlabel('Value of Perf-Const', fontsize=TEXT_SIZE_XYLABEL)
            ax4.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)
            ax4.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
            ax4.set_yticks([0, 200, 400, 600])
            ax4.set_ylim(0, 600)
            ax4.legend(frameon=False, fontsize=TEXT_SIZE_LEGEND)
            
            ax4.spines['top'].set_visible(False)
            ax4.spines['right'].set_visible(False)
            ax4.spines['left'].set_linewidth(1)
            ax4.spines['bottom'].set_linewidth(1)

    fig.tight_layout()
    
    # Ensure all subplots have the same height, bottom alignment, and equal width (25% each)
    # Get positions of all axes
    ax1_bbox = ax1.get_position()
    ax2_bbox = ax2.get_position()
    ax3_bbox = ax3.get_position()
    ax4_bbox = ax4.get_position()
    
    # Use the minimum bottom and the first subplot's height as standard
    min_bottom = min(ax1_bbox.y0, ax2_bbox.y0, ax3_bbox.y0, ax4_bbox.y0)
    standard_height = ax1_bbox.height
    
    # Calculate total width range (from leftmost x0 to rightmost x1)
    min_x0 = min(ax1_bbox.x0, ax2_bbox.x0, ax3_bbox.x0, ax4_bbox.x0)
    max_x1 = max(ax1_bbox.x1, ax2_bbox.x1, ax3_bbox.x1, ax4_bbox.x1)
    total_width = max_x1 - min_x0
    
    subplot_width = total_width * 0.25
    
    # Use a small fixed spacing between subplots (2% of total width)
    spacing = total_width * 0.02
    
    # Calculate the starting x position to center the four subplots
    total_subplot_width = 4 * subplot_width + 3 * spacing
    start_x = min_x0 + (total_width - total_subplot_width) / 2.0
    
    # Set all axes to have the same bottom, height, and width (25% each)
    ax1.set_position([start_x, min_bottom, subplot_width, standard_height])
    ax2.set_position([start_x + subplot_width + spacing, min_bottom, subplot_width, standard_height])
    ax3.set_position([start_x + 2 * (subplot_width + spacing), min_bottom, subplot_width, standard_height])
    ax4.set_position([start_x + 3 * (subplot_width + spacing), min_bottom, subplot_width, standard_height])
    
    out_dir = os.path.dirname(out_pdf)
    out_name = os.path.basename(out_pdf).replace('.pdf', '')
    plot_common.save_fig(out_dir, out_name)
    plt.close(fig)
    print(f"[ok] Saved: {out_pdf}")

def create_cs1_plot(softirq_csv, out_pdf):
    """Create cs1.pdf with softirq plot only"""
    if not os.path.exists(softirq_csv):
        print(f"[skip] {softirq_csv} not found")
        return
    
    # Width ratio: 25% of total (assuming total width 20, this is 5)
    # Adjusted aspect ratio: make it wider by reducing height
    fig, ax = plt.subplots(figsize=(5, HEIGHT))
    
    # Read CSV file
    max_restart = []
    worst_lat = []
    cpu_util = []
    with open(softirq_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['MAX_SOFTIRQ_TIME'] == '2ms':
                max_restart.append(int(row['MAX_SOFTIRQ_RESTART']))
                worst_lat.append(float(row['WorstLatUs']))
                cpu_util.append(float(row['CpuUtilPct']))
    
    if max_restart:
        # Sort by MAX_SOFTIRQ_RESTART
        sorted_data = sorted(zip(max_restart, worst_lat, cpu_util))
        max_restart = [x[0] for x in sorted_data]
        worst_lat = [x[1] for x in sorted_data]
        cpu_util = [x[2] for x in sorted_data]

        color1 = palette[0]
        ax.set_ylabel('Worst Latency (us)', color='black', fontsize=TEXT_SIZE_XYLABEL)
        ax.plot(max_restart, worst_lat, 
                 marker=plot_common.markers[0], color=color1, linewidth=2, markersize=10, label='Worst Latency')
        ax.tick_params(axis='y', labelcolor='black', labelsize=TEXT_SIZE_XYAXIS)
        ax.tick_params(axis='x', labelcolor='black', labelsize=TEXT_SIZE_XYAXIS, length=TICK_LENGTH_X, width=TICK_WIDTH_X)
        ax.set_ylim(bottom=0)
        ax.set_yticks([0, 250, 500, 700])
        ax.set_xticks([1, 5, 10, 15, 20])
        ax.set_xlabel('Value of Perf-Const', fontsize=TEXT_SIZE_XYLABEL)
        ax.axvline(x=10, color='black', linestyle='--', linewidth=2, alpha=0.7)
        ax.text(9.4, ax.get_ylim()[1] * 0.95, 'Default Value', ha='center', va='top', color='black', fontsize=TEXT_SIZE_XYAXIS)

        ax_twin = ax.twinx()
        color2 = palette[2]
        ax_twin.set_ylabel('CPU Usage (%)', color='black', fontsize=TEXT_SIZE_XYLABEL)
        ax_twin.plot(max_restart, cpu_util, 
                     marker=plot_common.markers[2], color=color2, linewidth=2, markersize=10, label='CPU Usage')
        ax_twin.tick_params(axis='y', labelcolor='black', labelsize=TEXT_SIZE_XYAXIS)
        ax_twin.set_yticks([0, 25, 50, 75, 100])
        ax_twin.set_ylim(0, 100)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('black')
        ax.spines['bottom'].set_color('black')
        ax_twin.spines['top'].set_visible(False)
        ax_twin.spines['left'].set_visible(False)
        ax_twin.spines['right'].set_color('black')
        ax_twin.spines['bottom'].set_color('black')

        # Combine legends and place above the plot
        handles1, labels1 = ax.get_legend_handles_labels()
        handles2, labels2 = ax_twin.get_legend_handles_labels()
        all_handles = handles1 + handles2
        all_labels = labels1 + labels2
        ax.legend(all_handles, all_labels, loc='upper center', bbox_to_anchor=(0.5, 1.4), ncol=2, frameon=False, fontsize=TEXT_SIZE_LEGEND)

    fig.tight_layout(rect=[0, 0, 1, 1.1])
    
    # Make x-axis tick label "10" bold (after tight_layout to ensure labels are set)
    for label in ax.get_xticklabels():
        if label.get_text() == '10':
            label.set_fontweight('bold')
    out_dir = os.path.dirname(out_pdf)
    out_name = os.path.basename(out_pdf).replace('.pdf', '')
    plot_common.save_fig(out_dir, out_name)
    plt.close(fig)
    print(f"[ok] Saved: {out_pdf}")

def create_cs2_plot(shrink_dir, out_pdf):
    """Create cs2.pdf with shrink plot only"""
    if not os.path.isdir(shrink_dir):
        print(f"[skip] {shrink_dir} not found")
        return
    
    # Width ratio: 30% of total (assuming total width 20, this is 6)
    fig, ax = plt.subplots(figsize=(6, HEIGHT))
    
    all_dt_us, all_cpu_usage, labels = process_shrink_files(shrink_dir)
    
    if labels:
        p50 = [max(x[0], 1) for x in all_dt_us]
        p90 = [max(x[1], 1) for x in all_dt_us]
        p99 = [max(x[2], 1) for x in all_dt_us]

        width = 0.2
        x = np.arange(len(labels))

        ax.bar(x - width, p50, label='P50', color=palette[2], width=width, zorder=2)
        ax.bar(x, p90, label='P90', color=palette[3], width=width, zorder=2)
        ax.bar(x + width, p99, label='P99', color=palette[1], width=width, zorder=2)

        ax.set_ylabel('Delta Time (μs)', fontsize=TEXT_SIZE_XYLABEL)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=TEXT_SIZE_XYAXIS, ha='center')
        ax.set_xlabel('Value of Perf-Const', fontsize=TEXT_SIZE_XYLABEL)
        ax.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)
        # Make x-axis tick label "128" bold
        for tick in ax.xaxis.get_major_ticks():
            if tick.label1.get_text() == '128':
                tick.label1.set_fontweight('bold')
        ax.set_yscale('log')
        ax.yaxis.set_major_locator(LogLocator(base=10, numticks=20))
        ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=100))
        ax.tick_params(axis='y', which='major', length=8, width=2, labelsize=TEXT_SIZE_XYAXIS)
        ax.tick_params(axis='y', which='minor', length=4, width=1.5)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(1)
        ax.spines['bottom'].set_linewidth(1)

        ax_twin = ax.twinx()
        ax_twin.plot(labels, all_cpu_usage, label='CPU Usage', color=palette[0], linewidth=2, marker=plot_common.markers[0], markersize=10, zorder=1)
        ax_twin.set_ylabel('CPU Usage (%)', fontsize=TEXT_SIZE_XYLABEL)
        ax_twin.set_ylim(0, 100)
        ax_twin.tick_params(axis='y', length=10, width=2, labelsize=TEXT_SIZE_XYAXIS)
        
        handles1, labels1 = ax.get_legend_handles_labels()
        handles2, labels2 = ax_twin.get_legend_handles_labels()
        all_handles = handles1 + handles2
        all_labels = labels1 + labels2
        
        ax.legend(all_handles, all_labels, loc='upper left', bbox_to_anchor=(-0.01, 0.93), frameon=False, fontsize=TEXT_SIZE_LEGEND)
        
        ax_twin.spines['top'].set_visible(False)
        ax_twin.spines['right'].set_linewidth(1)

        # Add black dashed box around x=128 (Default Value)
        if '128' in labels:
            idx_128 = labels.index('128')
            x_pos = x[idx_128]
            # Calculate bar positions: x - width, x, x + width
            bar_left = x_pos - width - width * 0.1  # Add some padding
            bar_right = x_pos + width + width * 0.1  # Add some padding
            box_width = bar_right - bar_left
            # Get y limits and max bar value for this x position
            y_bottom = ax.get_ylim()[0]
            y_top = ax.get_ylim()[1]
            # Find the maximum bar height at this position
            max_bar_value = max(p50[idx_128], p90[idx_128], p99[idx_128])
            # Calculate box height: use 20% of the max bar value, with minimum height
            if ax.get_yscale() == 'log':
                # For log scale, use a multiplier
                box_height = max_bar_value * 0.3
            else:
                box_height = max((y_top - y_bottom) * 0.15, max_bar_value * 0.2)
            box_height = max_bar_value * 1.3
            # Draw rectangle with black dashed border
            # box_width = box_width * 1.7
            # bar_left = bar_left * 0.97
            # rect = Rectangle((bar_left, y_bottom), box_width, box_height,
            #                linewidth=2, edgecolor='black', facecolor='none', 
            #                linestyle='--', zorder=3)
            # ax.add_patch(rect)
            # Add "Default Value" text above the box

    fig.tight_layout()
    out_dir = os.path.dirname(out_pdf)
    out_name = os.path.basename(out_pdf).replace('.pdf', '')
    plot_common.save_fig(out_dir, out_name)
    plt.close(fig)
    print(f"[ok] Saved: {out_pdf}")

def create_cs3_plot(migr_lat_dir, migr_tlb_dir, out_pdf):
    """Create cs3.pdf with migr_lat and migr_tlb plots"""
    # Width ratio: 45% of total (assuming total width 20, this is 9)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, HEIGHT))
    
    # Plot 1: migr_lat
    lat_txt_files = sorted(glob.glob(os.path.join(migr_lat_dir, '*.txt')), key=_extract_number_from_filename)
    if lat_txt_files:
        lat_labels = []
        p50_values, p90_values, p95_values, p99_values = [], [], [], []

        for path in lat_txt_files:
            stats = parse_latency_data(path)
            if not stats:
                continue
            m = re.search(r'(\d+)', os.path.basename(path))
            label = m.group(1) if m else os.path.basename(path)
            lat_labels.append(label)
            p50_values.append(stats['p50'])
            p90_values.append(stats['p90'])
            p95_values.append(stats['p95'])
            p99_values.append(stats['p99'])

        if lat_labels:
            # Convert to milliseconds
            p50 = np.asarray(p50_values, dtype=float) / 1000.0
            p90 = np.asarray(p90_values, dtype=float) / 1000.0
            p95 = np.asarray(p95_values, dtype=float) / 1000.0
            p99 = np.asarray(p99_values, dtype=float) / 1000.0

            x = np.arange(len(lat_labels))
            width_lat = 0.2

            r1 = ax1.bar(x - 1.5 * width_lat, p50, width_lat, label='P50', color=palette[3], zorder=2)
            r2 = ax1.bar(x - 0.5 * width_lat, p90, width_lat, label='P90', color=palette[4], zorder=2)
            r3 = ax1.bar(x + 0.5 * width_lat, p95, width_lat, label='P95', color=palette[2], zorder=2)
            r4 = ax1.bar(x + 1.5 * width_lat, p99, width_lat, label='P99', color=palette[1], zorder=2)

            ax1.set_ylabel('Latency (ms)', fontsize=TEXT_SIZE_XYLABEL)
            ax1.set_xticks(x)
            ax1.set_xticklabels(lat_labels, rotation=0, ha="center", fontsize=TEXT_SIZE_XYAXIS)
            ax1.set_xlabel('Value of Perf-Const', fontsize=TEXT_SIZE_XYLABEL)
            ax1.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)
            # Make x-axis tick label "512" bold
            for tick in ax1.xaxis.get_major_ticks():
                if tick.label1.get_text() == '512':
                    tick.label1.set_fontweight('bold')

            # Set fixed y-axis ticks: 0, 2, 4, 6
            ax1.set_ylim(0, 6)
            ax1.set_yticks([0, 2, 4, 6])
            ax1.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)

            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.spines['left'].set_linewidth(1)
            ax1.spines['bottom'].set_linewidth(1)

            ax1.legend(loc='upper left', frameon=False, fontsize=TEXT_SIZE_LEGEND, ncol=2)

            # Add black dashed box around x=512 (Default Value) for migr_lat
            if '512' in lat_labels:
                idx_512 = lat_labels.index('512')
                x_pos = x[idx_512]
                # Calculate bar positions: x - 1.5*width, x - 0.5*width, x + 0.5*width, x + 1.5*width
                bar_left = x_pos - 1.5 * width_lat - width_lat * 0.1  # Add some padding
                bar_right = x_pos + 1.5 * width_lat + width_lat * 0.1  # Add some padding
                box_width = bar_right - bar_left
                # Get y limits
                y_bottom = ax1.get_ylim()[0]
                y_top = ax1.get_ylim()[1]
                box_height = (y_top - y_bottom) * 0.15
                
                # box_height = box_height * 4.6
                # box_width = box_width * 1.5
                # bar_left = bar_left * 0.96
                # # Draw rectangle with black dashed border
                # rect = Rectangle((bar_left, y_bottom), box_width, box_height,
                #                linewidth=2, edgecolor='black', facecolor='none', 
                #                linestyle='--', zorder=3)
                # ax1.add_patch(rect)
                # Add "Default Value" text above the box

    # Plot 2: migr_tlb
    tlb_paths = sorted(glob.glob(os.path.join(migr_tlb_dir, "*.txt")))
    if tlb_paths:
        tlb_rows = []
        for p in tlb_paths:
            res = parse_tlb_file(p)
            if res:
                tlb_rows.append((res[0], res[1], res[2]))
        
        if tlb_rows:
            tlb_rows.sort(key=lambda x: x[0])
            tlb_labels = [str(row[0]) for row in tlb_rows]
            reason1_values = [row[1] / 1000.0 for row in tlb_rows]
            reason4_values = [row[2] / 1000.0 for row in tlb_rows]

            x = np.arange(len(tlb_labels))
            width = 0.35

            rects1 = ax2.bar(x - width/2, reason1_values, width, label='CPU TLB Shootdown',
                            color=palette[2], zorder=2)
            rects2 = ax2.bar(x + width/2, reason4_values, width, label='Remote IPI Send',
                            color=palette[3], zorder=2)

            ax2.set_ylabel('Count (K)', fontsize=TEXT_SIZE_XYLABEL)
            ax2.set_xticks(x)
            ax2.set_xticklabels(tlb_labels, fontsize=TEXT_SIZE_XYAXIS)
            ax2.set_xlabel('Value of Perf-Const', fontsize=TEXT_SIZE_XYLABEL)
            ax2.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)
            # Make x-axis tick label "512" bold
            for tick in ax2.xaxis.get_major_ticks():
                if tick.label1.get_text() == '512':
                    tick.label1.set_fontweight('bold')
            ax2.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
            ax2.set_yticks([0, 200, 400, 600])
            ax2.set_ylim(0, 600)
            ax2.legend(frameon=False, fontsize=TEXT_SIZE_LEGEND)
            
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_linewidth(1)
            ax2.spines['bottom'].set_linewidth(1)

            # Add black dashed box around x=512 (Default Value) for migr_tlb
            if '512' in tlb_labels:
                idx_512 = tlb_labels.index('512')
                x_pos = x[idx_512]
                # Calculate bar positions: x - width/2, x + width/2
                bar_left = x_pos - width/2 - width * 0.1  # Add some padding
                bar_right = x_pos + width/2 + width * 0.1  # Add some padding
                box_width = bar_right - bar_left
                # Get y limits
                y_bottom = ax2.get_ylim()[0]
                y_top = ax2.get_ylim()[1]
                box_height = (y_top - y_bottom) * 0.15
                # Draw rectangle with black dashed border
                # rect = Rectangle((bar_left, y_bottom), box_width, box_height,
                #                linewidth=2, edgecolor='black', facecolor='none', 
                #                linestyle='--', zorder=3)
                # ax2.add_patch(rect)
                # Add "Default Value" text above the box

    fig.tight_layout()
    out_dir = os.path.dirname(out_pdf)
    out_name = os.path.basename(out_pdf).replace('.pdf', '')
    plot_common.save_fig(out_dir, out_name)
    plt.close(fig)
    print(f"[ok] Saved: {out_pdf}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Default paths
    migr_lat_dir = os.path.join(script_dir, 'migr_data')
    migr_tlb_dir = os.path.join(script_dir, 'migr_tlb_data')
    softirq_csv = os.path.join(script_dir, 'softirq.csv')
    shrink_dir = os.path.join(script_dir, 'shrink_data')
    
    # Generate three separate PDFs
    create_cs1_plot(softirq_csv, os.path.join(script_dir, 'cs1.pdf'))
    create_cs2_plot(shrink_dir, os.path.join(script_dir, 'cs2.pdf'))
    create_cs3_plot(migr_lat_dir, migr_tlb_dir, os.path.join(script_dir, 'cs3.pdf'))

if __name__ == "__main__":
    main()

