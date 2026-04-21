#!/usr/bin/env python3
"""Plot Figure 18: Per-task transition delay CDF — Linux KLP vs XKernel.

Reads per-task transition data and produces a CDF plot showing the
distribution of per-task transition delays for 128 iperf3 threads.

Input files (in results/):
  per_task_data.txt    — KLP per-task data (legacy format)
  per_task_data_xk.txt — XKernel per-task data (legacy format)

Usage:
    python3 plot/plot.py                    # auto-detect results/
    python3 plot/plot.py path/to/results    # specific results dir
"""
import re
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
import os
import sys
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_common

palette = sns.color_palette("mako")

TEXT_SIZE_XYLABEL = 23
TEXT_SIZE_XYAXIS = 23
TEXT_SIZE_LEGEND = 23
TEXT_SIZE_ANNOTATE = 20


def parse_linux_klp_data(file_path):
    """Parse Linux KLP data from file."""
    with open(file_path, 'r') as f:
        raw_data = f.read()
    waited_ns = []
    for line in raw_data.strip().split('\n'):
        match = re.search(r'Waited: (\d+) ns', line)
        if match:
            waited_ns.append(int(match.group(1)))
    return np.array([x / 1000.0 for x in waited_ns])  # to microseconds


def parse_xkernel_data(file_path):
    """Parse Xkernel data from file.
    Supports both legacy format (差值：X us) and new format (Waited: X ns)."""
    with open(file_path, 'r') as f:
        raw_data = f.read()
    waited_us = []
    for line in raw_data.strip().split('\n'):
        # New format: "Waited: X ns" (includes BPF load time)
        match = re.search(r'Waited: (\d+) ns', line)
        if match:
            waited_us.append(int(match.group(1)) / 1000.0)
            continue
        # Legacy format: "差值：X us"
        match = re.search(r'\u5dee\u503c\uff1a(\d+) us', line)
        if match:
            waited_us.append(int(match.group(1)))
    return np.array(waited_us)


def calculate_cdf(data):
    """Calculate CDF for given data."""
    data_sorted = np.sort(data)
    n = len(data_sorted)
    cdf_percent = np.arange(1, n + 1) / n
    return data_sorted, cdf_percent


def plot_figure18(results_dir):
    klp_file = os.path.join(results_dir, 'per_task_data.txt')
    xk_file = os.path.join(results_dir, 'per_task_data_xk.txt')

    for f in [klp_file, xk_file]:
        if not os.path.exists(f):
            print(f"[skip] {f} not found")
            return

    klp_data = parse_linux_klp_data(klp_file)
    xk_data = parse_xkernel_data(xk_file)

    klp_sorted, klp_cdf = calculate_cdf(klp_data)
    xk_sorted, xk_cdf = calculate_cdf(xk_data)

    klp_p50 = np.median(klp_data)
    xk_p50 = np.median(xk_data)

    # ── Print summary table ──────────────────────────────────────────
    def fmt_delay(us):
        if us >= 1_000_000:
            return f"{us/1_000_000:.1f} s"
        elif us >= 1000:
            return f"{us/1000:.1f} ms"
        else:
            return f"{us:.1f} µs"

    klp_p99 = np.percentile(klp_data, 99)
    xk_p99 = np.percentile(xk_data, 99)

    print()
    print("=" * 62)
    print(f"  {'Metric':<24} {'Linux KLP':>16}  {'XKernel':>16}")
    print("-" * 62)
    print(f"  {'P50 delay':<24} {fmt_delay(klp_p50):>16}  {fmt_delay(xk_p50):>16}")
    print(f"  {'P99 delay':<24} {fmt_delay(klp_p99):>16}  {fmt_delay(xk_p99):>16}")
    speedup = klp_p50 / max(xk_p50, 0.001)
    print(f"  {'Speedup (P50)':<24} {f'{speedup:.0f}x':>16}")
    print("=" * 62)

    # ── CDF plot ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9.5, 4))

    ax.plot(klp_sorted, klp_cdf, color=palette[1], linewidth=2,
            label='Linux KLP',
            marker=plot_common.markers[0], markersize=2, zorder=2)
    ax.plot(xk_sorted, xk_cdf, color=palette[3], linewidth=2,
            label='Xkernel',
            marker=plot_common.markers[2], markersize=2, zorder=2)

    ax.set_xscale('log')
    ax.set_xlabel('Transition Delay (\u03bcs)', fontsize=TEXT_SIZE_XYLABEL)
    ax.set_ylabel('CDF (%)', fontsize=TEXT_SIZE_XYLABEL)
    ax.tick_params(axis='x', length=10, width=2, labelsize=TEXT_SIZE_XYAXIS)
    ax.tick_params(axis='y', length=10, width=2, labelsize=TEXT_SIZE_XYAXIS)
    ax.grid(True, alpha=0.3, zorder=0)
    ax.set_ylim(0, 1)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])

    def y_formatter(x, pos):
        return f'{int(x * 100)}'
    ax.yaxis.set_major_formatter(FuncFormatter(y_formatter))
    ax.legend(loc='best', frameon=False, fontsize=TEXT_SIZE_LEGEND)

    # Annotate load time (max delay = total transition span)
    klp_max = np.max(klp_data)
    xk_max = np.max(xk_data)

    ax.axvline(x=klp_max, color=palette[1], linestyle='--',
               linewidth=2, alpha=0.7, zorder=1)
    ax.axvline(x=xk_max, color=palette[3], linestyle='--',
               linewidth=2, alpha=0.7, zorder=1)

    # Format labels
    if klp_max >= 1000:
        klp_label = f'load time: {klp_max/1000:.1f}ms'
    else:
        klp_label = f'load time: {klp_max:.0f}\u03bcs'
    if xk_max >= 1000:
        xk_label = f'load time: {xk_max/1000:.1f}ms'
    else:
        xk_label = f'load time: {xk_max:.0f}\u03bcs'

    ax.annotate(klp_label, xy=(klp_max, 0.9),
                xytext=(klp_max * 1.5, 0.9),
                arrowprops=dict(arrowstyle='->', color=palette[1], lw=1.5),
                fontsize=TEXT_SIZE_ANNOTATE, color=palette[1],
                ha='left', va='center')
    ax.annotate(xk_label, xy=(xk_max, 0.9),
                xytext=(xk_max * 1.5, 0.9),
                arrowprops=dict(arrowstyle='->', color=palette[3], lw=1.5),
                fontsize=TEXT_SIZE_ANNOTATE, color=palette[3],
                ha='left', va='center')

    # P50 annotations
    ax.axvline(x=klp_p50, color=palette[1], linestyle=':',
               linewidth=2, alpha=0.7, zorder=1)
    ax.axvline(x=xk_p50, color=palette[3], linestyle=':',
               linewidth=2, alpha=0.7, zorder=1)

    if klp_p50 >= 1000:
        klp_p50_text = f'P50: {klp_p50/1000:.1f}ms'
    else:
        klp_p50_text = f'P50: {klp_p50:.1f}\u03bcs'
    ax.annotate(klp_p50_text, xy=(klp_p50, 0.5),
                xytext=(klp_p50 * 1.5, 0.5),
                arrowprops=dict(arrowstyle='->', color=palette[1], lw=1.5),
                fontsize=TEXT_SIZE_ANNOTATE, color=palette[1],
                ha='left', va='center')

    if xk_p50 >= 1000:
        xk_p50_text = f'P50: {xk_p50/1000:.1f}ms'
    else:
        xk_p50_text = f'P50: {xk_p50:.1f}\u03bcs'
    ax.annotate(xk_p50_text, xy=(xk_p50, 0.5),
                xytext=(xk_p50 * 1.5, 0.5),
                arrowprops=dict(arrowstyle='->', color=palette[3], lw=1.5),
                fontsize=TEXT_SIZE_ANNOTATE, color=palette[3],
                ha='left', va='center')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)

    plt.tight_layout()

    plot_dir = os.path.dirname(os.path.abspath(__file__))
    plot_common.save_fig(plot_dir, 'figure18')
    print(f"\n[ok] Plot saved to {plot_dir}/figure18.pdf")
    plt.close()


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        results_dir = os.path.join(script_dir, '..', 'results')

    results_dir = os.path.abspath(results_dir)
    print(f"Using results from: {results_dir}")
    plot_figure18(results_dir)
