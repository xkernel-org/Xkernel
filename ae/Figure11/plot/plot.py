#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot Figure 11: NUMA migration probe latency under different
NR_MAX_BATCHED_MIGRATION values.

Reads result files from the results directory, each named <batch_value>.txt.
Parses the summarized probe latency percentiles (P50/P90/P95/P99) appended
by summarize.py.

Produces a grouped bar chart of probe latency (µs) with
NR_MAX_BATCHED_MIGRATION values on the x-axis.

Usage:
    python plot/plot.py                          # auto-detect latest results
    python plot/plot.py results/20251126-034820  # specific results dir
"""
import os
import re
import sys
import glob
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

palette = sns.color_palette("mako", 8)
COLOR_P50 = palette[1]
COLOR_P90 = palette[3]
COLOR_P95 = palette[4]
COLOR_P99 = palette[6]

script_dir = os.path.dirname(os.path.abspath(__file__))
figure_dir = os.path.join(script_dir, '..')

SEPARATOR = '************************************'


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


def _clean_float(s):
    return float(s.replace(',', ''))


def _pick_probe_block(content):
    """Extract the last summarized probe latency block."""
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
    """Parse probe latency percentiles from a result file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw = f.read()

        block = _pick_probe_block(raw)

        p50 = re.search(r'\bP50\s*,\s*([\d,]+(?:\.\d+)?)', block)
        p90 = re.search(r'\bP90\s*,\s*([\d,]+(?:\.\d+)?)', block)
        p95 = re.search(r'\bP95\s*,\s*([\d,]+(?:\.\d+)?)', block)
        p99 = re.search(r'\bP99\s*,\s*([\d,]+(?:\.\d+)?)', block)

        if not all([p50, p90, p95, p99]):
            print(f"[warn] Missing Pxx in: {filepath}", file=sys.stderr)
            return None

        return {
            'p50': _clean_float(p50.group(1)),
            'p90': _clean_float(p90.group(1)),
            'p95': _clean_float(p95.group(1)),
            'p99': _clean_float(p99.group(1)),
        }
    except Exception as e:
        print(f"[error] {filepath}: {e}", file=sys.stderr)
        return None


def process_results(results_dir):
    """Process all result files, return sorted labels and latency stats."""
    labels = []
    stats_list = []

    for fname in os.listdir(results_dir):
        if not fname.endswith('.txt') or fname == 'log.txt':
            continue
        batch_val = fname.replace('.txt', '')
        try:
            int(batch_val)
        except ValueError:
            continue

        filepath = os.path.join(results_dir, fname)
        stats = parse_latency_data(filepath)
        if not stats:
            continue

        labels.append(batch_val)
        stats_list.append(stats)

    # Sort by numeric value
    sorted_indices = sorted(range(len(labels)), key=lambda i: int(labels[i]))
    labels = [labels[i] for i in sorted_indices]
    stats_list = [stats_list[i] for i in sorted_indices]

    return labels, stats_list


def plot_figure11(labels, stats_list):
    """Create Figure 11: probe latency bar chart."""
    p50 = [s['p50'] for s in stats_list]
    p90 = [s['p90'] for s in stats_list]
    p95 = [s['p95'] for s in stats_list]
    p99 = [s['p99'] for s in stats_list]

    fig, ax = plt.subplots(figsize=(10, 5))

    width = 0.18
    x = np.arange(len(labels))

    ax.bar(x - 1.5 * width, p50, width, label='P50', color=COLOR_P50, zorder=2)
    ax.bar(x - 0.5 * width, p90, width, label='P90', color=COLOR_P90, zorder=2)
    ax.bar(x + 0.5 * width, p95, width, label='P95', color=COLOR_P95, zorder=2)
    ax.bar(x + 1.5 * width, p99, width, label='P99', color=COLOR_P99, zorder=2)

    ax.set_xlabel('NR_MAX_BATCHED_MIGRATION', fontsize=TEXT_SIZE_XYLABEL)
    ax.set_ylabel('Probe Latency (µs)', fontsize=TEXT_SIZE_XYLABEL)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=TEXT_SIZE_XYAXIS)
    ax.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
    ax.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X)
    ax.grid(True, which='major', axis='y', linestyle='--', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(loc='upper left', frameon=False, fontsize=TEXT_SIZE_LEGEND)

    plt.tight_layout()
    plot_common.save_fig(script_dir, 'figure11')
    plt.close(fig)
    print(f"[✓] Saved: {script_dir}/figure11.pdf")


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
    labels, stats_list = process_results(results_dir)

    if not labels:
        print("Error: No valid result files found.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Found {len(labels)} NR_MAX_BATCHED_MIGRATION values: {', '.join(labels)}")
    for label, s in zip(labels, stats_list):
        print(f"    NR_MAX_BATCHED_MIGRATION={label:>5s}  "
              f"P50={s['p50']:>8.1f}  P90={s['p90']:>8.1f}  "
              f"P95={s['p95']:>8.1f}  P99={s['p99']:>8.1f} µs")

    plot_figure11(labels, stats_list)


if __name__ == '__main__':
    main()
