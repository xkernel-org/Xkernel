import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

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

def process_files(directory):
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

    # Sort by integer value of label (assuming labels are numeric strings like '1', '10', '100')
    sorted_labels = sorted(labels, key=lambda x: int(x))
    sorted_dt_us = [all_dt_us[labels.index(label)] for label in sorted_labels]
    sorted_cpu_usage = [all_cpu_usage[labels.index(label)] for label in sorted_labels]

    return sorted_dt_us, sorted_cpu_usage, sorted_labels

def plot_graphs(all_dt_us, all_cpu_usage, labels):
    fig, ax1 = plt.subplots(figsize=(8, 4))

    p50 = [x[0] for x in all_dt_us]
    p90 = [x[1] for x in all_dt_us]
    p99 = [x[2] for x in all_dt_us]
    
    # Avoid log(0) — replace any non-positive value with a small positive number (e.g., 1)
    p50 = [max(v, 1) for v in p50]
    p90 = [max(v, 1) for v in p90]
    p99 = [max(v, 1) for v in p99]

    width = 0.2
    x = np.arange(len(labels))

    ax1.bar(x - width, p50, label='P50', color=plot_common.colors[2], edgecolor='black', linewidth=1, width=width, zorder=2)
    ax1.bar(x, p90, label='P90', color=plot_common.colors[4], edgecolor='black', linewidth=1, width=width, zorder=2)
    ax1.bar(x + width, p99, label='P99', color=plot_common.colors[1], edgecolor='black', linewidth=1, width=width, zorder=2)

    ax1.set_xlabel('SHRINK_BATCH')
    ax1.set_ylabel('Delta Time (μs)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.tick_params(axis='x', length=0, width=0)
    ax1.set_yscale('log')
    # Set more y-axis ticks for log scale
    ax1.yaxis.set_major_locator(LogLocator(base=10, numticks=20))
    ax1.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=100))
    # Make ticks more visible
    ax1.tick_params(axis='y', which='major', length=8, width=2)
    ax1.tick_params(axis='y', which='minor', length=4, width=1.5)
    ax1.tick_params(axis='x', length=0, width=0)
    
    # Remove top and right spines
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    # Make axis lines thicker
    ax1.spines['left'].set_linewidth(1)
    ax1.spines['bottom'].set_linewidth(1)

    ax2 = ax1.twinx()
    ax2.plot(labels, all_cpu_usage, label='CPU Usage', color=plot_common.colors[0], linewidth=2, marker=plot_common.markers[0], markersize=10, zorder=1)
    ax2.set_ylabel('CPU Usage (%)')
    ax2.set_ylim(0, 100)
    ax2.tick_params(axis='y', length=10, width=2)
    
    # Combine legends from both axes
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    all_handles = handles1 + handles2
    all_labels = labels1 + labels2
    
    # Create combined legend
    legend = ax1.legend(all_handles, all_labels, loc='upper left', bbox_to_anchor=(0, 0.7), frameon=True, facecolor='white', framealpha=1.0)
    legend.set_zorder(10)
    legend.get_frame().set_zorder(10)
    
    # Remove top and right spines for ax2
    ax2.spines['top'].set_visible(False)
    # Make axis lines thicker
    ax2.spines['right'].set_linewidth(1)

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    return fig

def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else './shrink_data'

    all_dt_us, all_cpu_usage, labels = process_files(directory)

    fig = plot_graphs(all_dt_us, all_cpu_usage, labels)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plot_common.save_fig(script_dir, 'shrink')
    plt.close(fig)

if __name__ == "__main__":
    main()