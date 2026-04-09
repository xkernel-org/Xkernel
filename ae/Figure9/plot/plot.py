#!/usr/bin/env python3
"""Plot Figure 9: Worst latency & CPU usage vs MAX_SOFTIRQ_RESTART."""
import csv
import os
import sys

import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_common

TEXT_SIZE_XYLABEL = 20
TEXT_SIZE_XYAXIS = 20
TEXT_SIZE_LEGEND = 20
TICK_LENGTH_X = 5
TICK_WIDTH_X = 1
HEIGHT = 3.5

palette = sns.color_palette("mako")

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, '..', 'results', 'figure9.csv')
out_pdf = os.path.join(script_dir, 'figure9.pdf')


def plot_figure9(softirq_csv, out_pdf):
    if not os.path.exists(softirq_csv):
        print(f"[skip] {softirq_csv} not found")
        return

    fig, ax = plt.subplots(figsize=(5, HEIGHT))

    # Read CSV — average across repetitions per MAX_SOFTIRQ_RESTART value
    from collections import defaultdict
    buckets = defaultdict(lambda: {'worst': [], 'avg': [], 'cpu': []})
    with open(softirq_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = int(row['MAX_SOFTIRQ_RESTART'])
            buckets[val]['worst'].append(float(row['WorstLatUs']))
            buckets[val]['avg'].append(float(row['AvgLatUs']))
            buckets[val]['cpu'].append(float(row['CpuUtilPct']))

    if not buckets:
        print("[skip] No data in CSV")
        return

    sorted_vals = sorted(buckets.keys())
    max_restart = sorted_vals
    worst_lat = [sum(buckets[v]['worst']) / len(buckets[v]['worst']) for v in sorted_vals]
    cpu_util = [sum(buckets[v]['cpu']) / len(buckets[v]['cpu']) for v in sorted_vals]

    # Left axis: Worst Latency
    color1 = palette[0]
    ax.set_ylabel('Worst Latency (us)', color='black', fontsize=TEXT_SIZE_XYLABEL)
    ax.plot(max_restart, worst_lat,
            marker=plot_common.markers[0], color=color1, linewidth=2,
            markersize=10, label='Worst Latency')
    ax.tick_params(axis='y', labelcolor='black', labelsize=TEXT_SIZE_XYAXIS)
    ax.tick_params(axis='x', labelcolor='black', labelsize=TEXT_SIZE_XYAXIS,
                   length=TICK_LENGTH_X, width=TICK_WIDTH_X)
    ax.set_ylim(bottom=0)
    ax.set_yticks([0, 250, 500, 700])
    ax.set_xticks([1, 5, 10, 15, 20])
    ax.set_xlabel('Value of Perf-Const', fontsize=TEXT_SIZE_XYLABEL)
    ax.axvline(x=10, color='black', linestyle='--', linewidth=2, alpha=0.7)
    ax.text(9.4, ax.get_ylim()[1] * 0.95, 'Default Value',
            ha='center', va='top', color='black', fontsize=TEXT_SIZE_XYAXIS)

    # Right axis: CPU Usage
    ax_twin = ax.twinx()
    color2 = palette[2]
    ax_twin.set_ylabel('CPU Usage (%)', color='black', fontsize=TEXT_SIZE_XYLABEL)
    ax_twin.plot(max_restart, cpu_util,
                 marker=plot_common.markers[2], color=color2, linewidth=2,
                 markersize=10, label='CPU Usage')
    ax_twin.tick_params(axis='y', labelcolor='black', labelsize=TEXT_SIZE_XYAXIS)
    ax_twin.set_yticks([0, 25, 50, 75, 100])
    ax_twin.set_ylim(0, 100)

    # Spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('black')
    ax.spines['bottom'].set_color('black')
    ax_twin.spines['top'].set_visible(False)
    ax_twin.spines['left'].set_visible(False)
    ax_twin.spines['right'].set_color('black')
    ax_twin.spines['bottom'].set_color('black')

    # Legend above the plot
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax_twin.get_legend_handles_labels()
    ax.legend(handles1 + handles2, labels1 + labels2,
              loc='upper center', bbox_to_anchor=(0.5, 1.4),
              ncol=2, frameon=False, fontsize=TEXT_SIZE_LEGEND)

    fig.tight_layout(rect=[0, 0, 1, 1.1])

    # Bold the default value tick label
    for label in ax.get_xticklabels():
        if label.get_text() == '10':
            label.set_fontweight('bold')

    out_dir = os.path.dirname(out_pdf)
    out_name = os.path.basename(out_pdf).replace('.pdf', '')
    plot_common.save_fig(out_dir, out_name)
    plt.close(fig)
    print(f"[ok] Saved: {out_pdf}")


if __name__ == '__main__':
    plot_figure9(csv_path, out_pdf)
