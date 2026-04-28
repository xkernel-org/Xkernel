#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot Figure 11: NUMA migration probe latency and TLB shootdown counts
under different NR_MAX_BATCHED_MIGRATION values.

Reads result files from the results directory, each named <batch_value>.txt.
Parses the summarized probe latency percentiles (P50/P90/P95/P99) appended
by summarize.py.

Produces grouped bar charts with NR_MAX_BATCHED_MIGRATION values on the x-axis.
Default value (512) is bolded.

Usage:
    python plot/plot.py                    # use results/ directory
    python plot/plot.py path/to/results    # specific results dir
"""
import os
import re
import sys
import glob
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import plot_common

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import seaborn as sns

TEXT_SIZE = 18
TEXT_SIZE_XYLABEL = 20
TEXT_SIZE_XYAXIS = 20
TEXT_SIZE_LEGEND = 20
TICK_LENGTH_X = 5
TICK_WIDTH_X = 1
HEIGHT = 4.5

DEFAULT_VALUE = '512'

palette = sns.color_palette("mako", 8)

script_dir = os.path.dirname(os.path.abspath(__file__))
figure_dir = os.path.join(script_dir, '..')

SEPARATOR = '************************************'


def find_results_dir():
    """Return the results directory."""
    return os.path.join(figure_dir, 'results')


def _extract_number_from_filename(fname):
    m = re.search(r'(\d+)', os.path.basename(fname))
    return int(m.group(1)) if m else 10**9


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


def parse_tlb_data(filepath):
    """Parse tlb_flush reason counts from a bpftrace output file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            raw = f.read()

        reason1 = re.search(r'@tlb_reason_cnt\[1\]:\s*([\d,]+)', raw)
        reason4 = re.search(r'@tlb_reason_cnt\[4\]:\s*([\d,]+)', raw)

        if not all([reason1, reason4]):
            print(f"[warn] Missing @tlb_reason_cnt[1]/[4] in: {filepath}", file=sys.stderr)
            return None

        return {
            'reason1': int(reason1.group(1).replace(',', '')),
            'reason4': int(reason4.group(1).replace(',', '')),
        }
    except Exception as e:
        print(f"[error] {filepath}: {e}", file=sys.stderr)
        return None


def style_batch_axis(ax, labels):
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=TEXT_SIZE_XYAXIS)
    ax.set_xlabel('Value of Perf-Const', fontsize=TEXT_SIZE_XYLABEL)
    ax.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)

    for tick in ax.xaxis.get_major_ticks():
        if tick.label1.get_text() == DEFAULT_VALUE:
            tick.label1.set_fontweight('bold')


def style_spines(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)


def style_scientific_y_axis(ax):
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_scientific(True)
    formatter.set_powerlimits((0, 0))
    ax.yaxis.set_major_formatter(formatter)
    ax.yaxis.get_offset_text().set_fontsize(TEXT_SIZE_XYAXIS)


def plot_latency(results_dir):
    """Create Figure 11: probe latency bar chart."""
    if not os.path.isdir(results_dir):
        print(f"[skip] {results_dir} not found")
        return

    lat_txt_files = sorted(
        glob.glob(os.path.join(results_dir, '*.txt')),
        key=_extract_number_from_filename
    )

    lat_labels = []
    p50_values, p90_values, p95_values, p99_values = [], [], [], []

    for path in lat_txt_files:
        if os.path.basename(path) == 'log.txt':
            continue
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

    if not lat_labels:
        print("Error: No valid result files found.", file=sys.stderr)
        return

    print(f"[*] Found {len(lat_labels)} NR_MAX_BATCHED_MIGRATION values: {', '.join(lat_labels)}")
    for label, s50, s90, s95, s99 in zip(lat_labels, p50_values, p90_values, p95_values, p99_values):
        print(f"    NR_MAX_BATCHED_MIGRATION={label:>5s}  "
              f"P50={s50:>8.1f}  P90={s90:>8.1f}  "
              f"P95={s95:>8.1f}  P99={s99:>8.1f} µs")

    # Convert to milliseconds
    p50 = np.asarray(p50_values, dtype=float) / 1000.0
    p90 = np.asarray(p90_values, dtype=float) / 1000.0
    p95 = np.asarray(p95_values, dtype=float) / 1000.0
    p99 = np.asarray(p99_values, dtype=float) / 1000.0

    fig, ax = plt.subplots(figsize=(6, HEIGHT))

    x = np.arange(len(lat_labels))
    width = 0.2

    ax.bar(x - 1.5 * width, p50, width, label='P50', color=palette[3], zorder=2)
    ax.bar(x - 0.5 * width, p90, width, label='P90', color=palette[4], zorder=2)
    ax.bar(x + 0.5 * width, p95, width, label='P95', color=palette[2], zorder=2)
    ax.bar(x + 1.5 * width, p99, width, label='P99', color=palette[1], zorder=2)

    ax.set_ylabel('Latency (ms)', fontsize=TEXT_SIZE_XYLABEL)
    style_batch_axis(ax, lat_labels)

    ax.set_ylim(0, 6)
    ax.set_yticks([0, 2, 4, 6])
    ax.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)

    style_spines(ax)

    ax.legend(loc='upper left', frameon=False, fontsize=TEXT_SIZE_LEGEND, ncol=2)

    fig.tight_layout()
    plot_common.save_fig(script_dir, 'figure11')
    plt.close(fig)
    print(f"[✓] Saved: {script_dir}/figure11.pdf")


def plot_tlb_shootdown_count(results_dir):
    """Create Figure 11 companion chart: TLB shootdown counts."""
    tlb_dir = os.path.join(results_dir, 'tlb_shootdown_count')
    if not os.path.isdir(tlb_dir):
        print(f"[skip] {tlb_dir} not found")
        return

    txt_files = sorted(
        glob.glob(os.path.join(tlb_dir, '*.txt')),
        key=_extract_number_from_filename
    )

    labels = []
    remote_shootdown = []
    remote_ipi_send = []

    for path in txt_files:
        stats = parse_tlb_data(path)
        if not stats:
            continue
        m = re.search(r'(\d+)', os.path.basename(path))
        label = m.group(1) if m else os.path.basename(path)
        labels.append(label)
        remote_shootdown.append(stats['reason1'])
        remote_ipi_send.append(stats['reason4'])

    if not labels:
        print("[skip] No valid TLB shootdown result files found.", file=sys.stderr)
        return

    print(f"[*] Found {len(labels)} TLB shootdown result values: {', '.join(labels)}")
    for label, reason1, reason4 in zip(labels, remote_shootdown, remote_ipi_send):
        print(f"    NR_MAX_BATCHED_MIGRATION={label:>5s}  "
              f"reason[1]={reason1:>10,d}  reason[4]={reason4:>10,d}")

    fig, ax = plt.subplots(figsize=(6, HEIGHT))

    x = np.arange(len(labels))
    width = 0.35

    ax.bar(x - 0.5 * width, remote_shootdown, width,
           label='Remote shootdown', color=palette[3], zorder=2)
    ax.bar(x + 0.5 * width, remote_ipi_send, width,
           label='Remote IPI send', color=palette[1], zorder=2)

    ax.set_ylabel('TLB flush count', fontsize=TEXT_SIZE_XYLABEL)
    style_batch_axis(ax, labels)
    ax.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
    style_scientific_y_axis(ax)
    style_spines(ax)
    remote_legend_x = 0.12  # Move the Remote legend text group to the right.
    ax.legend(loc='upper left', bbox_to_anchor=(remote_legend_x, 1.0),
              frameon=False, fontsize=TEXT_SIZE_LEGEND, markerfirst=False)

    fig.tight_layout()
    plot_common.save_fig(script_dir, 'figure11_tlb_shootdown_count')
    plt.close(fig)
    print(f"[✓] Saved: {script_dir}/figure11_tlb_shootdown_count.pdf")


def plot_figure11(results_dir):
    plot_latency(results_dir)
    plot_tlb_shootdown_count(results_dir)


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
    plot_figure11(results_dir)


if __name__ == '__main__':
    main()
