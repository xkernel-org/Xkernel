#!/usr/bin/env python3
import os
import re
import sys
import glob
import matplotlib.pyplot as plt
import numpy as np

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Usage: 
# $ python plot/tlb_count.py ../res/tlb_shootdown_count/

PAT_REASON_1 = re.compile(r'@tlb_reason_cnt\[1\]:\s*([\d,]+)')
PAT_REASON_4 = re.compile(r'@tlb_reason_cnt\[4\]:\s*([\d,]+)')

def to_int(s: str) -> int:
    return int(s.replace(',', ''))

def parse_file(path: str):
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

def main():
    if len(sys.argv) >= 2:
        in_dir = sys.argv[1]
    else:
        in_dir = './migr_tlb_data'
    if not os.path.isdir(in_dir):
        print(f"Error: '{in_dir}' is not a directory")
        sys.exit(1)

    # Collect *.txt (non-recursive as requested)
    paths = sorted(glob.glob(os.path.join(in_dir, "*.txt")))
    if not paths:
        print(f"No .txt files found in {in_dir}")
        sys.exit(1)

    rows = []
    for p in paths:
        res = parse_file(p)
        if res:
            rows.append((res[0], res[1], res[2]))  # (batch_size, reason1, reason4)

    if not rows:
        print("Failed to parse any valid data. Exiting.")
        sys.exit(1)

    # Sort by batch_size
    rows.sort(key=lambda x: x[0])

    # Extract data
    x_labels = [str(row[0]) for row in rows]
    reason1_values = [row[1] / 1000.0 for row in rows]  # Convert to K
    reason4_values = [row[2] / 1000.0 for row in rows]  # Convert to K

    # --- Plot ---
    x = np.arange(len(x_labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 4))
    rects1 = ax.bar(x - width/2, reason1_values, width, label='CPU TLB Shootdown',
                    color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
    rects2 = ax.bar(x + width/2, reason4_values, width, label='Remote IPI Send',
                    color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)

    ax.set_ylabel('Count (K)')
    ax.set_xlabel('NR_MAX_BATCHED_MIGRATION')
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.tick_params(axis='x', length=0)
    ax.legend(frameon=True, facecolor='white', framealpha=1.0, fontsize=20)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Make axis lines thicker
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)

    fig.tight_layout()

    plot_common.save_fig(in_dir, "migr_tlb")

if __name__ == "__main__":
    main()