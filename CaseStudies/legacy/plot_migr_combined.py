# Combined plot for migr_lat and migr_tlb
import os
import re
import glob
import argparse
import numpy as np
import matplotlib.pyplot as plt
from math import ceil, log10, floor
from matplotlib.ticker import MaxNLocator
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

SEPARATOR = '************************************'

def _extract_number_from_filename(fname: str) -> int:
    m = re.search(r'(\d+)', os.path.basename(fname))
    return int(m.group(1)) if m else 10**9

def _clean_float(s: str) -> float:
    return float(s.replace(',', ''))

def to_int(s: str) -> int:
    return int(s.replace(',', ''))

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

PAT_REASON_1 = re.compile(r'@tlb_reason_cnt\[1\]:\s*([\d,]+)')
PAT_REASON_4 = re.compile(r'@tlb_reason_cnt\[4\]:\s*([\d,]+)')

def parse_tlb_file(path: str):
    """Return (batch_size, reason1, reason4) or None on failure."""
    base = os.path.splitext(os.path.basename(path))[0]
    try:
        batch_size = int(base)
    except ValueError:
        print(f"Skip: filename base '{base}' is not an integer batch size ({path})")
        return None

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: file not found {path}")
        return None

    m1 = PAT_REASON_1.search(content)
    m4 = PAT_REASON_4.search(content)
    if not (m1 and m4):
        print(f"Warning: missing reason[1]/reason[4] in {path}")
        return None

    try:
        r1 = to_int(m1.group(1))
        r4 = to_int(m4.group(1))
    except Exception as e:
        print(f"Warning: parse int failed in {path}: {e}")
        return None

    return (batch_size, r1, r4)

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

def create_combined_plot(lat_dir, tlb_dir, out_pdf):
    # Parse latency data
    lat_txt_files = sorted(glob.glob(os.path.join(lat_dir, '*.txt')), key=_extract_number_from_filename)
    if not lat_txt_files:
        print(f"[skip] No .txt in {lat_dir}")
        return

    lat_labels = []
    p50_values, p90_values, p95_values, p99_values = [], [], [], []

    for path in lat_txt_files:
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
        print(f"[skip] No valid latency data in {lat_dir}")
        return

    # Parse TLB data
    tlb_paths = sorted(glob.glob(os.path.join(tlb_dir, "*.txt")))
    if not tlb_paths:
        print(f"No .txt files found in {tlb_dir}")
        return

    tlb_rows = []
    for p in tlb_paths:
        res = parse_tlb_file(p)
        if res:
            tlb_rows.append((res[0], res[1], res[2]))

    if not tlb_rows:
        print("Failed to parse any valid TLB data. Exiting.")
        return

    tlb_rows.sort(key=lambda x: x[0])
    tlb_labels = [str(row[0]) for row in tlb_rows]
    reason1_values = [row[1] / 1000.0 for row in tlb_rows]  # Convert to K
    reason4_values = [row[2] / 1000.0 for row in tlb_rows]  # Convert to K

    # Ensure labels match (use common labels)
    # Use the intersection of labels from both datasets
    common_labels = sorted(set(lat_labels) & set(tlb_labels), key=int)
    if not common_labels:
        print("[warn] No common labels between latency and TLB data")
        # Use latency labels as primary
        common_labels = lat_labels

    # Filter data to common labels
    lat_indices = [lat_labels.index(l) for l in common_labels if l in lat_labels]
    tlb_indices = [tlb_labels.index(l) for l in common_labels if l in tlb_labels]

    p50_filtered = [p50_values[i] for i in lat_indices]
    p90_filtered = [p90_values[i] for i in lat_indices]
    p95_filtered = [p95_values[i] for i in lat_indices]
    p99_filtered = [p99_values[i] for i in lat_indices]

    reason1_filtered = [reason1_values[i] for i in tlb_indices]
    reason4_filtered = [reason4_values[i] for i in tlb_indices]

    # Convert latency to milliseconds
    p50 = np.asarray(p50_filtered, dtype=float) / 1000.0
    p90 = np.asarray(p90_filtered, dtype=float) / 1000.0
    p95 = np.asarray(p95_filtered, dtype=float) / 1000.0
    p99 = np.asarray(p99_filtered, dtype=float) / 1000.0

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
    
    x = np.arange(len(common_labels))
    width_lat = 0.2
    width_tlb = 0.35

    # Top subplot: Latency
    r1 = ax1.bar(x - 1.5 * width_lat, p50, width_lat, label='P50', color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
    r2 = ax1.bar(x - 0.5 * width_lat, p90, width_lat, label='P90', color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)
    r3 = ax1.bar(x + 0.5 * width_lat, p95, width_lat, label='P95', color=plot_common.colors[1], edgecolor='black', linewidth=1, zorder=2)
    r4 = ax1.bar(x + 1.5 * width_lat, p99, width_lat, label='P99', color=plot_common.colors[0], edgecolor='black', linewidth=1, zorder=2)

    ax1.set_ylabel('Latency (ms)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(common_labels, rotation=0, ha="center")
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
    # No xlabel for top subplot

    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_linewidth(1)
    ax1.spines['bottom'].set_linewidth(1)

    ax1.legend(loc='upper left', frameon=True, facecolor='white', framealpha=1.0, fontsize=20, ncol=2)

    # Bottom subplot: TLB
    rects1 = ax2.bar(x - width_tlb/2, reason1_filtered, width_tlb, label='CPU TLB Shootdown',
                    color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
    rects2 = ax2.bar(x + width_tlb/2, reason4_filtered, width_tlb, label='Remote IPI Send',
                    color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)

    ax2.set_ylabel('Count (K)')
    ax2.set_xlabel('NR_MAX_BATCHED_MIGRATION')
    ax2.set_xticks(x)
    ax2.set_xticklabels(common_labels)
    ax2.tick_params(axis='x', length=0)
    ax2.set_yticks([0, 200, 400, 600])
    ax2.set_ylim(0, 600)
    ax2.legend(frameon=True, facecolor='white', framealpha=1.0, fontsize=20)
    
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_linewidth(1)
    ax2.spines['bottom'].set_linewidth(1)

    fig.tight_layout()
    plt.subplots_adjust(hspace=0.2)
    out_dir = os.path.dirname(out_pdf)
    out_name = os.path.basename(out_pdf).replace('.pdf', '')
    plot_common.save_fig(out_dir, out_name)
    plt.close(fig)
    print(f"[ok] Saved: {out_pdf}")

def main():
    parser = argparse.ArgumentParser(description="Combine migr_lat and migr_tlb plots")
    parser.add_argument("-l", "--lat-dir", type=str, default="./migr_data", help="Directory for latency data")
    parser.add_argument("-t", "--tlb-dir", type=str, default="./migr_tlb_data", help="Directory for TLB data")
    parser.add_argument("-o", "--output", type=str, default="./migr_combined.pdf", help="Output PDF file")
    args = parser.parse_args()

    lat_dir = os.path.abspath(os.path.expanduser(args.lat_dir))
    tlb_dir = os.path.abspath(os.path.expanduser(args.tlb_dir))

    if not os.path.isdir(lat_dir):
        print(f"Error: '{lat_dir}' is not a directory")
        return
    if not os.path.isdir(tlb_dir):
        print(f"Error: '{tlb_dir}' is not a directory")
        return

    create_combined_plot(lat_dir, tlb_dir, args.output)

if __name__ == "__main__":
    main()

