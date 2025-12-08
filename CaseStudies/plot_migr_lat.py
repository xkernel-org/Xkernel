# plot_probe_latency_per_dir.py
import os
import re
import glob
import argparse
import numpy as np
import matplotlib.pyplot as plt
from math import ceil, log10, floor
from matplotlib.ticker import MultipleLocator, MaxNLocator
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Usage:
# $ python draw.py -i ../res/high_migrate_load/2-migrates/

SEPARATOR = '************************************'

def _extract_number_from_filename(fname: str) -> int:
    m = re.search(r'(\d+)', os.path.basename(fname))
    return int(m.group(1)) if m else 10**9

def _clean_float(s: str) -> float:
    return float(s.replace(',', ''))

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

# TLB parsing functions
PAT_REASON_1 = re.compile(r'@tlb_reason_cnt\[1\]:\s*([\d,]+)')
PAT_REASON_4 = re.compile(r'@tlb_reason_cnt\[4\]:\s*([\d,]+)')

def to_int(s: str) -> int:
    return int(s.replace(',', ''))

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

def create_bar_chart(labels, p50_values, p90_values, p95_values, p99_values, out_pdf, title, tlb_dir=None):
    labels = list(labels)
    p50 = np.asarray(p50_values, dtype=float)
    p90 = np.asarray(p90_values, dtype=float)
    p95 = np.asarray(p95_values, dtype=float)
    p99 = np.asarray(p99_values, dtype=float)

    # conver to milliseconds
    p50 = p50 / 1000.0
    p90 = p90 / 1000.0
    p95 = p95 / 1000.0
    p99 = p99 / 1000.0

    # Try to load TLB data if directory is provided
    tlb_data_available = False
    tlb_labels = []
    reason1_values = []
    reason4_values = []
    
    if tlb_dir and os.path.isdir(tlb_dir):
        tlb_paths = sorted(glob.glob(os.path.join(tlb_dir, "*.txt")))
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
            tlb_data_available = True

    # Use common labels if TLB data is available
    if tlb_data_available:
        common_labels = sorted(set(labels) & set(tlb_labels), key=int)
        if common_labels:
            # Filter to common labels
            lat_indices = [labels.index(l) for l in common_labels if l in labels]
            tlb_indices = [tlb_labels.index(l) for l in common_labels if l in tlb_labels]
            
            labels = common_labels
            p50 = p50[lat_indices]
            p90 = p90[lat_indices]
            p95 = p95[lat_indices]
            p99 = p99[lat_indices]
            reason1_values = [reason1_values[i] for i in tlb_indices]
            reason4_values = [reason4_values[i] for i in tlb_indices]
        else:
            tlb_data_available = False

    x = np.arange(len(labels))
    width_lat = 0.2
    width_tlb = 0.35

    if tlb_data_available:
        # Create combined plot with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
    else:
        # Single plot (original behavior)
        fig, ax1 = plt.subplots(figsize=(8, 4))
        ax2 = None

    # Top subplot: Latency
    r1 = ax1.bar(x - 1.5 * width_lat, p50, width_lat, label='P50', color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
    r2 = ax1.bar(x - 0.5 * width_lat, p90, width_lat, label='P90', color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)
    r3 = ax1.bar(x + 0.5 * width_lat, p95, width_lat, label='P95', color=plot_common.colors[1], edgecolor='black', linewidth=1, zorder=2)
    r4 = ax1.bar(x + 1.5 * width_lat, p99, width_lat, label='P99', color=plot_common.colors[0], edgecolor='black', linewidth=1, zorder=2)

    ax1.set_ylabel('Latency (ms)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=0, ha="center")
    ax1.tick_params(axis='x', length=0)

    ymax_data = float(max(p50.max(initial=0), p90.max(initial=0), p95.max(initial=0), p99.max(initial=0)))
    goal_ticks = 6
    step = _nice_step(ymax_data, goal_ticks=goal_ticks)

    HEADROOM_FRAC = 0.06   
    y_top_aligned = ceil(ymax_data / step) * step
    y_top = y_top_aligned + HEADROOM_FRAC * ymax_data
    y_top = min(y_top, ymax_data * 1.08)

    ax1.set_ylim(0, y_top)
    ax1.yaxis.set_major_locator(MaxNLocator(nbins=goal_ticks, steps=[1, 2, 5, 10]))
    
    if tlb_data_available:
        # No xlabel for top subplot when combined
        pass
    else:
        ax1.set_xlabel('NR_MAX_BATCHED_MIGRATION')

    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_linewidth(1)
    ax1.spines['bottom'].set_linewidth(1)

    ax1.legend(loc='upper left', frameon=True, facecolor='white', framealpha=1.0, fontsize=20)

    # Bottom subplot: TLB (if available)
    if tlb_data_available and ax2:
        rects1 = ax2.bar(x - width_tlb/2, reason1_values, width_tlb, label='CPU TLB Shootdown',
                        color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
        rects2 = ax2.bar(x + width_tlb/2, reason4_values, width_tlb, label='Remote IPI Send',
                        color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)

        ax2.set_ylabel('Count (K)')
        ax2.set_xlabel('NR_MAX_BATCHED_MIGRATION')
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels)
        ax2.tick_params(axis='x', length=0)
        ax2.set_yticks([0, 200, 400, 600])
        ax2.set_ylim(0, 600)
        ax2.legend(frameon=True, facecolor='white', framealpha=1.0, fontsize=20)
        
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_linewidth(1)
        ax2.spines['bottom'].set_linewidth(1)

    fig.tight_layout()
    if tlb_data_available:
        plt.subplots_adjust(hspace=0.15)
    out_dir = os.path.dirname(out_pdf)
    out_name = os.path.basename(out_pdf).replace('.pdf', '')
    plot_common.save_fig(out_dir, out_name)
    plt.close(fig)
    print(f"[ok] Saved: {out_pdf}")

def process_one_dir(d: str, out_root: str):
    txt_files = sorted(glob.glob(os.path.join(d, '*.txt')), key=_extract_number_from_filename)
    if not txt_files:
        print(f"[skip] No .txt in {d}")
        return

    labels = []
    p50_values, p90_values, p95_values, p99_values = [], [], [], []

    for path in txt_files:
        stats = parse_latency_data(path)
        if not stats:
            continue
        m = re.search(r'(\d+)', os.path.basename(path))
        label = m.group(1) if m else os.path.basename(path)
        labels.append(label)
        p50_values.append(stats['p50'])
        p90_values.append(stats['p90'])
        p95_values.append(stats['p95'])
        p99_values.append(stats['p99'])

    if not labels:
        print(f"[skip] No valid latency data in {d}")
        return

    # Try to find TLB data directory (sibling directory)
    tlb_dir = None
    parent_dir = os.path.dirname(d)
    if parent_dir:
        tlb_dir_candidate = os.path.join(parent_dir, 'migr_tlb_data')
        if os.path.isdir(tlb_dir_candidate):
            tlb_dir = tlb_dir_candidate
        else:
            # Try relative to script location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            tlb_dir_candidate = os.path.join(script_dir, 'migr_tlb_data')
            if os.path.isdir(tlb_dir_candidate):
                tlb_dir = tlb_dir_candidate

    out_pdf = os.path.join(out_root, f"migr_lat.pdf")
    title = f"{os.path.basename(d)}: Probe latency percentiles by batch"
    create_bar_chart(labels, p50_values, p90_values, p95_values, p99_values, out_pdf, title, tlb_dir=tlb_dir)

def parse_args():
    ap = argparse.ArgumentParser(
        description="Parse probe latency percentiles from logs and plot per-subdir bar charts."
    )
    ap.add_argument(
        "-i", "--input",
        type=str,
        default="./migr_data",
        help=""
    )
    return ap.parse_args()

def main():
    args = parse_args()
    base = os.path.abspath(os.path.expanduser(args.input))

    if not os.path.exists(base) or not os.path.isdir(base):
        print(f"[error] Input path is not a directory: {base}")
        return

    subdirs = [os.path.join(base, x) for x in os.listdir(base) if os.path.isdir(os.path.join(base, x))]

    preferred = [d for d in subdirs if re.search(r'-migrates$', os.path.basename(d))]
    candidates = preferred if preferred else subdirs

    any_done = False
    for d in sorted(candidates, key=lambda s: _extract_number_from_filename(s)):
        if glob.glob(os.path.join(d, '*.txt')):
            process_one_dir(d, out_root=base)
            any_done = True

    if not any_done:
        txt_here = glob.glob(os.path.join(base, '*.txt'))
        if txt_here:
            process_one_dir(base, out_root=base)
        else:
            print("[info] No subdirectories with .txt found, and no .txt in the input directory.")

if __name__ == "__main__":
    main()