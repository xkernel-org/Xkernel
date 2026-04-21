#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot Figure 10: zswap shrinker latency under different SHRINK_BATCH values.

Reads result files from the results directory, each named <batch_value>.txt.
Each line has format: iter=N dmajflt=M dt_us=T
The last few lines contain `time` output with CPU usage (e.g., "12%CPU").

Produces a grouped bar chart of P50/P90/P99 delta time (µs, log scale)
with a twin-axis CPU usage line, SHRINK_BATCH values on the x-axis.
The default value (128) x-tick label is bolded.

Usage:
    python plot/plot.py                    # use results/ directory
    python plot/plot.py path/to/results    # specific results dir
"""
import os
import re
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import plot_common

import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator
import seaborn as sns

TEXT_SIZE = 18
TEXT_SIZE_XYLABEL = 20
TEXT_SIZE_XYAXIS = 20
TEXT_SIZE_LEGEND = 20
TICK_LENGTH_X = 5
TICK_WIDTH_X = 1
HEIGHT = 4.5

DEFAULT_VALUE = '128'

palette = sns.color_palette("mako", 6)

script_dir = os.path.dirname(os.path.abspath(__file__))
figure_dir = os.path.join(script_dir, '..')


def find_results_dir():
    """Return the results directory."""
    return os.path.join(figure_dir, 'results')


def extract_data_from_file(filepath):
    """Extract dt_us values and CPU usage from a result file."""
    dt_us = []
    cpu_usage = []

    with open(filepath) as f:
        for line in f:
            if 'dt_us=' in line:
                parts = line.split()
                for part in parts:
                    if part.startswith('dt_us='):
                        dt_us.append(int(part.split('=')[1]))
            elif 'elapsed' in line:
                m = re.search(r'([\d.]+)%CPU', line)
                if m:
                    cpu_usage.append(float(m.group(1)))

    return dt_us, cpu_usage


def process_results(results_dir):
    """Process all result files, return sorted percentiles, cpu usage, and labels."""
    all_dt_us = []
    all_cpu_usage = []
    labels = []

    for fname in os.listdir(results_dir):
        if not fname.endswith('.txt') or fname == 'log.txt':
            continue
        batch_val = fname.replace('.txt', '')
        try:
            int(batch_val)
        except ValueError:
            continue

        filepath = os.path.join(results_dir, fname)
        dt_us, cpu_usage = extract_data_from_file(filepath)
        if not dt_us:
            print(f"Warning: no data in {fname}", file=sys.stderr)
            continue

        p50 = np.percentile(dt_us, 50)
        p90 = np.percentile(dt_us, 90)
        p99 = np.percentile(dt_us, 99)

        labels.append(batch_val)
        all_dt_us.append((p50, p90, p99))
        all_cpu_usage.append(np.mean(cpu_usage) if cpu_usage else 0)

    # Sort by numeric value
    sorted_labels = sorted(labels, key=lambda x: int(x))
    sorted_dt_us = [all_dt_us[labels.index(l)] for l in sorted_labels]
    sorted_cpu = [all_cpu_usage[labels.index(l)] for l in sorted_labels]

    return sorted_dt_us, sorted_cpu, sorted_labels


def plot_figure10(results_dir):
    """Create Figure 10: delta time bar chart + CPU usage line."""
    if not os.path.isdir(results_dir):
        print(f"[skip] {results_dir} not found")
        return

    fig, ax = plt.subplots(figsize=(6, HEIGHT))

    all_dt_us, all_cpu_usage, labels = process_results(results_dir)

    if not labels:
        print("Error: No valid result files found.", file=sys.stderr)
        plt.close(fig)
        return

    # ── Summary table (matches README Expected Results) ─────────────
    print()
    print("=" * 72)
    print("  Figure 10 — Zswap Shrinker Latency (SHRINK_BATCH)")
    print("=" * 72)
    print(f"  {'SHRINK_BATCH':>12} {'P50 (µs)':>12} {'P90 (µs)':>12} {'P99 (µs)':>12} {'CPU (%)':>10}")
    print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*10}")
    for label, (p50, p90, p99), cpu in zip(labels, all_dt_us, all_cpu_usage):
        default_marker = " *" if label == DEFAULT_VALUE else ""
        cpu_str = f"{cpu:.0f}%" if cpu else "N/A"
        print(f"  {label:>12s} {p50:>12.0f} {p90:>12.0f} {p99:>12.0f} {cpu_str:>10}{default_marker}")
    print("=" * 72)
    print("  (* = kernel default)")
    print()

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

    # Bold the default value tick label
    for tick in ax.xaxis.get_major_ticks():
        if tick.label1.get_text() == DEFAULT_VALUE:
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

    # Twin axis for CPU usage
    ax_twin = ax.twinx()
    ax_twin.plot(labels, all_cpu_usage, label='CPU Usage', color=palette[0],
                 linewidth=2, marker=plot_common.markers[0], markersize=10, zorder=1)
    ax_twin.set_ylabel('CPU Usage (%)', fontsize=TEXT_SIZE_XYLABEL)
    ax_twin.set_ylim(0, 100)
    ax_twin.tick_params(axis='y', length=10, width=2, labelsize=TEXT_SIZE_XYAXIS)
    ax_twin.spines['top'].set_visible(False)
    ax_twin.spines['right'].set_linewidth(1)

    # Combined legend
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax_twin.get_legend_handles_labels()
    ax.legend(handles1 + handles2, labels1 + labels2,
              loc='upper left', bbox_to_anchor=(-0.01, 0.93),
              frameon=False, fontsize=TEXT_SIZE_LEGEND)

    fig.tight_layout()
    plot_common.save_fig(script_dir, 'figure10')
    plt.close(fig)
    print(f"[✓] Saved: {script_dir}/figure10.pdf")


def main():
    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        results_dir = find_results_dir()

    if not results_dir or not os.path.isdir(results_dir):
        print("Error: No results directory found.", file=sys.stderr)
        print("Usage: python plot/plot.py [results_dir]", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Reading results from: {results_dir}")
    plot_figure10(results_dir)


if __name__ == '__main__':
    main()
