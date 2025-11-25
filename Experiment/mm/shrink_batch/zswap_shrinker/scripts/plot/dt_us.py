import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import sys

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
    fig, ax1 = plt.subplots(figsize=(12, 7))

    p50 = [x[0] for x in all_dt_us]
    p90 = [x[1] for x in all_dt_us]
    p99 = [x[2] for x in all_dt_us]
    
    # Avoid log(0) — replace any non-positive value with a small positive number (e.g., 1)
    p50 = [max(v, 1) for v in p50]
    p90 = [max(v, 1) for v in p90]
    p99 = [max(v, 1) for v in p99]

    width = 0.2
    x = np.arange(len(labels))

    ax1.bar(x - width, p50, label='P50', alpha=0.7, color='b', width=width)
    ax1.bar(x, p90, label='P90', alpha=0.7, color='g', width=width)
    ax1.bar(x + width, p99, label='P99', alpha=0.7, color='r', width=width)

    ax1.set_xlabel('SHRINK_BATCH')
    # ax1.set_ylabel('dt_us (log scale)')
    ax1.set_ylabel('Latency per Iteration (μs, log scale)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_yscale('log') 
    ax1.grid(True, which="major", axis='y', linestyle='--', linewidth=0.5)
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(labels, all_cpu_usage, label='CPU Usage (%)', color='purple', marker='o')
    ax2.set_ylabel('CPU Usage (%)')
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper right')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    return fig

def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else '/users/yltang/Xkernel/Experiment/shrink_batch/zswap_shrinker/res/dt_us'

    all_dt_us, all_cpu_usage, labels = process_files(directory)

    with PdfPages('output_graphs.pdf') as pdf:
        fig = plot_graphs(all_dt_us, all_cpu_usage, labels)
        pdf.savefig(fig)
        plt.close(fig)

if __name__ == "__main__":
    main()