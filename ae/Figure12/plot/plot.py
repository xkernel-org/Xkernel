#!/usr/bin/env python3
"""Plot Figure 12: NGINX FCT tail latency under different TCP CUBIC scaling factors.

Compares vanilla kernel (SF=3, default) vs. KernelX adaptive SF policy
under 20ms and 80ms RTT scenarios.

Usage:
    python plot/plot.py                    # auto-detect results/
    python plot/plot.py path/to/results    # specific results dir
"""
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import seaborn as sns
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_common

# Unified color palette
palette = sns.color_palette("mako")

# Text sizes
TEXT_SIZE_XLABEL = 18
TEXT_SIZE_YLABEL = 18
TEXT_SIZE_XYAXIS = 18
TEXT_SIZE_LEGEND = 18


def parse_histogram_file(file_path):
    """Parse HistogramLogProcessor / wrk2 percentile output file.

    Expected format (whitespace-separated):
        Value   Percentile   TotalCount   1/(1-Percentile)

    Auto-detects unit: if median value < 1000, assumes ms; else assumes µs.
    Returns values in milliseconds.
    """
    raw_values = []
    percentiles = []
    inv_one_minus_p = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('Value'):
                continue

            parts = line.split()
            if len(parts) >= 4:
                try:
                    value = float(parts[0])
                    percentile = float(parts[1])
                    inv_p_str = parts[3]
                    if inv_p_str.lower() == 'inf':
                        inv_p = float('inf')
                    else:
                        inv_p = float(inv_p_str)
                    raw_values.append(value)
                    percentiles.append(percentile)
                    inv_one_minus_p.append(inv_p)
                except (ValueError, IndexError):
                    continue

    raw_values = np.array(raw_values)
    # Auto-detect unit: if median < 1000, assume values are already in ms;
    # otherwise assume µs and convert to ms
    if len(raw_values) > 0 and np.median(raw_values) >= 1000:
        values_ms = raw_values / 1_000.0  # µs → ms
    else:
        values_ms = raw_values  # already ms

    return values_ms, np.array(percentiles), np.array(inv_one_minus_p)


def get_latency_at_percentile(values_ms, percentiles, target_percentile):
    """Return latency (in seconds) at the closest percentile >= target."""
    idx = np.searchsorted(percentiles, target_percentile, side='left')
    if idx >= len(values_ms):
        idx = len(values_ms) - 1
    return values_ms[idx] / 1_000.0


def plot_figure12(results_dir):
    """Plot Figure 12: tail latency comparison."""
    # Locate data files
    file_vanilla_20ms = os.path.join(results_dir, 'vanilla_20ms.txt')
    file_vanilla_80ms = os.path.join(results_dir, 'vanilla_80ms.txt')
    file_xkernel_20ms = os.path.join(results_dir, 'xkernel_20ms.txt')
    file_xkernel_80ms = os.path.join(results_dir, 'xkernel_80ms.txt')

    # Check all files exist
    for f in [file_vanilla_20ms, file_vanilla_80ms, file_xkernel_20ms, file_xkernel_80ms]:
        if not os.path.exists(f):
            print(f"[skip] {f} not found")
            return

    # Parse data
    vals_v20, pcts_v20, inv_v20 = parse_histogram_file(file_vanilla_20ms)
    vals_v80, pcts_v80, inv_v80 = parse_histogram_file(file_vanilla_80ms)
    vals_x20, pcts_x20, inv_x20 = parse_histogram_file(file_xkernel_20ms)
    vals_x80, pcts_x80, inv_x80 = parse_histogram_file(file_xkernel_80ms)

    # Print P999 and P9999 latencies
    targets = {'P99.9': 0.999, 'P99.99': 0.9999}
    datasets = {
        'Vanilla (20ms)':      (vals_v20, pcts_v20),
        'Vanilla (80ms)':      (vals_v80, pcts_v80),
        'Adaptive SF (20ms)':  (vals_x20, pcts_x20),
        'Adaptive SF (80ms)':  (vals_x80, pcts_x80),
    }

    print("\n=== Tail Latency (FCT in seconds) ===")
    for name, (vals, pcts) in datasets.items():
        print(f"\n{name}:")
        for label, p in targets.items():
            latency_sec = get_latency_at_percentile(vals, pcts, p)
            print(f"  {label}: {latency_sec:.6f} s")

    # Apply masks for visualization
    p9999_inv_p_max = 11000.0

    def apply_mask(values_ms, inv_p, max_inv_p):
        mask = np.isfinite(inv_p) & (inv_p <= max_inv_p)
        return inv_p[mask], values_ms[mask]  # values already in ms

    x_v20, y_v20 = apply_mask(vals_v20, inv_v20, p9999_inv_p_max)
    x_v80, y_v80 = apply_mask(vals_v80, inv_v80, p9999_inv_p_max)
    x_x20, y_x20 = apply_mask(vals_x20, inv_x20, p9999_inv_p_max)
    x_x80, y_x80 = apply_mask(vals_x80, inv_x80, p9999_inv_p_max)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(8, 3))

    ax.set_xscale('log')
    ax.set_yscale('linear')
    ax.set_xlim([1.0, 11000.0])

    # Auto-scale y-axis based on data
    all_y = np.concatenate([y for y in [y_v20, y_v80, y_x20, y_x80] if len(y) > 0])
    y_max_val = np.max(all_y) if len(all_y) > 0 else 70
    y_max = max(70, int(np.ceil(y_max_val / 20) * 20 + 20))  # round up to next 20
    ax.set_ylim([0, y_max])

    key_inv_p = [1.0, 10.0, 100.0, 1000.0, 10000.0]
    key_labels = ['0', 'p90', 'p99', 'p99.9', 'p99.99']
    ax.set_xticks(key_inv_p)
    ax.set_xticklabels(key_labels, fontsize=TEXT_SIZE_XYAXIS)

    y_ticks = list(range(0, y_max, max(20, y_max // 5)))
    ax.set_yticks(y_ticks)
    ax.tick_params(axis='both', labelsize=TEXT_SIZE_XYAXIS)

    # Plot data
    # SF=3: light gray, thick; Adaptive SF: black, thin with markers
    # 20ms: solid; 80ms: dashed
    WIDTH = 1.15
    line_objects = {}

    if len(x_v20) > 0:
        line, = ax.plot(x_v20, y_v20,
                        color='#B0B0B0', linewidth=4, label='SF=3 (20ms)',
                        zorder=2, linestyle='-')
        line_objects['SF=3 (20ms)'] = line

    if len(x_x20) > 0:
        line, = ax.plot(x_x20, y_x20,
                        color='black', linestyle='-', linewidth=WIDTH,
                        label='Adaptive SF (20ms)', zorder=2,
                        marker='o', markersize=2.5,
                        markeredgecolor='black', markerfacecolor='black',
                        markevery=5)
        line_objects['Adaptive SF (20ms)'] = line

    if len(x_v80) > 0:
        line, = ax.plot(x_v80, y_v80,
                        color='#B0B0B0', linewidth=4, label='SF=3 (80ms)',
                        zorder=2, linestyle='--')
        line_objects['SF=3 (80ms)'] = line

    if len(x_x80) > 0:
        line, = ax.plot(x_x80, y_x80,
                        color='black', linestyle='--', linewidth=WIDTH,
                        label='Adaptive SF (80ms)', zorder=2,
                        marker='o', markersize=2.5,
                        markeredgecolor='black', markerfacecolor='black',
                        markevery=5)
        line_objects['Adaptive SF (80ms)'] = line

    ax.set_xlabel('Percentile', fontsize=TEXT_SIZE_XLABEL)
    ax.set_ylabel('FCT (ms)', fontsize=TEXT_SIZE_YLABEL)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--', zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)

    # Create legend with custom handles (thinner for SF=3)
    ordered_labels = [
        'SF=3 (20ms)',
        'SF=3 (80ms)',
        'Adaptive SF (20ms)',
        'Adaptive SF (80ms)'
    ]

    all_handles = []
    all_labels = []
    for label in ordered_labels:
        if label not in line_objects:
            continue
        original_line = line_objects[label]
        if label.startswith('SF=3'):
            lw = 2.0
            ls = original_line.get_linestyle()
            handle_len = 0.92 if '80ms' in label else 1.0
            legend_handle = Line2D([0, handle_len], [0, 0],
                                   color=original_line.get_color(),
                                   linestyle=ls, linewidth=lw, label=label)
        else:
            legend_handle = Line2D([0, 0.92], [0, 0],
                                   color=original_line.get_color(),
                                   linestyle=original_line.get_linestyle(),
                                   linewidth=original_line.get_linewidth(),
                                   marker=original_line.get_marker(),
                                   markersize=original_line.get_markersize(),
                                   markeredgecolor=original_line.get_markeredgecolor(),
                                   markerfacecolor=original_line.get_markerfacecolor(),
                                   label=label)
        all_handles.append(legend_handle)
        all_labels.append(label)

    ax.legend(all_handles, all_labels, loc='upper left',
              bbox_to_anchor=(0.005, 0.995), ncol=1, frameon=False,
              fontsize=TEXT_SIZE_LEGEND, handlelength=1)

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)

    plot_dir = os.path.dirname(os.path.abspath(__file__))
    plot_common.save_fig(plot_dir, 'figure12')
    print(f"\n[ok] Plot saved to {plot_dir}/figure12.pdf")
    plt.close()


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        results_dir = os.path.join(script_dir, '..', 'results')

    results_dir = os.path.abspath(results_dir)
    print(f"Using results from: {results_dir}")
    plot_figure12(results_dir)
