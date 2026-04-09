#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot Figure 10: zswap shrinker latency under different SHRINK_BATCH values.

Reads result files from the results directory, each named <batch_value>.txt.
Each line has format: iter=N dmajflt=M dt_us=T

Produces a grouped bar chart of P50/P90/P99 latency per iteration (µs)
on a log scale, with SHRINK_BATCH values on the x-axis.

Usage:
    python plot/plot.py                          # auto-detect latest results
    python plot/plot.py results/20251126-034820  # specific results dir
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import plot_common

import matplotlib.pyplot as plt
import seaborn as sns

TEXT_SIZE = 18
TEXT_SIZE_XYLABEL = 20
TEXT_SIZE_XYAXIS = 20
TEXT_SIZE_LEGEND = 20
TICK_LENGTH_X = 5
TICK_WIDTH_X = 1

palette = sns.color_palette("mako", 6)
COLOR_P50 = palette[1]
COLOR_P90 = palette[3]
COLOR_P99 = palette[5]

script_dir = os.path.dirname(os.path.abspath(__file__))
figure_dir = os.path.join(script_dir, '..')


def find_latest_results():
    """Find the most recent results subdirectory."""
    results_base = os.path.join(figure_dir, 'results')
    if not os.path.isdir(results_base):
        return None
    subdirs = sorted([
        d for d in os.listdir(results_base)
        if os.path.isdir(os.path.join(results_base, d))
    ])
    return os.path.join(results_base, subdirs[-1]) if subdirs else None


def extract_dt_us(filepath):
    """Extract dt_us values from a result file."""
    dt_us = []
    with open(filepath) as f:
        for line in f:
            if 'dt_us=' in line:
                for part in line.split():
                    if part.startswith('dt_us='):
                        dt_us.append(int(part.split('=')[1]))
    return dt_us


def process_results(results_dir):
    """Process all result files, return sorted labels and percentiles."""
    labels = []
    percentiles = []

    for fname in os.listdir(results_dir):
        if not fname.endswith('.txt') or fname == 'log.txt':
            continue
        batch_val = fname.replace('.txt', '')
        try:
            int(batch_val)
        except ValueError:
            continue

        filepath = os.path.join(results_dir, fname)
        dt_us = extract_dt_us(filepath)
        if not dt_us:
            print(f"Warning: no data in {fname}", file=sys.stderr)
            continue

        p50 = np.percentile(dt_us, 50)
        p90 = np.percentile(dt_us, 90)
        p99 = np.percentile(dt_us, 99)

        labels.append(batch_val)
        percentiles.append((p50, p90, p99))

    # Sort by numeric value
    sorted_indices = sorted(range(len(labels)), key=lambda i: int(labels[i]))
    labels = [labels[i] for i in sorted_indices]
    percentiles = [percentiles[i] for i in sorted_indices]

    return labels, percentiles


def plot_figure10(labels, percentiles):
    """Create Figure 10: latency bar chart."""
    p50 = [max(p[0], 1) for p in percentiles]
    p90 = [max(p[1], 1) for p in percentiles]
    p99 = [max(p[2], 1) for p in percentiles]

    fig, ax = plt.subplots(figsize=(8, 4.5))

    width = 0.22
    x = np.arange(len(labels))

    ax.bar(x - width, p50, width, label='P50', color=COLOR_P50, zorder=2)
    ax.bar(x,         p90, width, label='P90', color=COLOR_P90, zorder=2)
    ax.bar(x + width, p99, width, label='P99', color=COLOR_P99, zorder=2)

    ax.set_xlabel('SHRINK_BATCH', fontsize=TEXT_SIZE_XYLABEL)
    ax.set_ylabel('Latency per Iteration (µs, log)', fontsize=TEXT_SIZE_XYLABEL)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=TEXT_SIZE_XYAXIS)
    ax.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
    ax.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X)
    ax.set_yscale('log')
    ax.grid(True, which='major', axis='y', linestyle='--', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(loc='upper left', frameon=False, fontsize=TEXT_SIZE_LEGEND)

    plt.tight_layout()
    plot_common.save_fig(script_dir, 'figure10')
    plt.close(fig)
    print(f"[✓] Saved: {script_dir}/figure10.pdf")


def main():
    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        results_dir = find_latest_results()

    if not results_dir or not os.path.isdir(results_dir):
        print("Error: No results directory found.", file=sys.stderr)
        print("Usage: python plot/plot.py [results_dir]", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Reading results from: {results_dir}")
    labels, percentiles = process_results(results_dir)

    if not labels:
        print("Error: No valid result files found.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Found {len(labels)} SHRINK_BATCH values: {', '.join(labels)}")
    for label, (p50, p90, p99) in zip(labels, percentiles):
        print(f"    SHRINK_BATCH={label:>4s}  P50={p50:>10.0f}  P90={p90:>10.0f}  P99={p99:>10.0f} µs")

    plot_figure10(labels, percentiles)


if __name__ == '__main__':
    main()
