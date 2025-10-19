#!/usr/bin/env python3
import os
import re
import sys
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
    if len(sys.argv) != 2:
        print("Usage: python plot.py <dir_with_txt>")
        print("Example: python plot.py ../res/tlb")
        sys.exit(1)

    in_dir = sys.argv[1]
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
            rows.append({"batch_size": res[0], "reason[1]": res[1], "reason[4]": res[2]})

    if not rows:
        print("Failed to parse any valid data. Exiting.")
        sys.exit(1)

    df = pd.DataFrame(rows).sort_values("batch_size").reset_index(drop=True)

    # --- Plot ---
    x_labels = df["batch_size"]
    x = np.arange(len(x_labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, df["reason[1]"], width, label='@tlb_reason_cnt[1]')
    rects2 = ax.bar(x + width/2, df["reason[4]"], width, label='@tlb_reason_cnt[4]')

    ax.set_ylabel('Count')
    ax.set_xlabel('NR_MAX_BATCHED_MIGRATION')
    ax.set_title('TLB Flush Counts by Reason and Batch Size')
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.legend()

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height}',
                        xy=(rect.get_x() + rect.get_width()/2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()

    out_path = os.path.join(in_dir, "tlb_flush_counts.png")
    plt.savefig(out_path)
    print(f"Chart saved to: {out_path}")

if __name__ == "__main__":
    main()