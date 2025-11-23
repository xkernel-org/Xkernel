# plot_probe_latency_per_dir.py
import os
import re
import glob
import argparse
import numpy as np
import matplotlib.pyplot as plt
from math import ceil, log10, floor
from matplotlib.ticker import MultipleLocator, MaxNLocator

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

def _fmt_val(v: float) -> str:
    return f"{v:.0f}" if v >= 100 else f"{v:.1f}"

def create_bar_chart(labels, p50_values, p90_values, p95_values, p99_values, out_pdf, title):
    labels = list(labels)
    p50 = np.asarray(p50_values, dtype=float)
    p90 = np.asarray(p90_values, dtype=float)
    p95 = np.asarray(p95_values, dtype=float)
    p99 = np.asarray(p99_values, dtype=float)

    x = np.arange(len(labels))
    width = 0.2

    fig, ax = plt.subplots(figsize=(12, 8))

    r1 = ax.bar(x - 1.5 * width, p50, width, label='P50')
    r2 = ax.bar(x - 0.5 * width, p90, width, label='P90')
    r3 = ax.bar(x + 0.5 * width, p95, width, label='P95')
    r4 = ax.bar(x + 1.5 * width, p99, width, label='P99')

    ax.set_ylabel('Latency (μs)')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, ha="center")

    ymax_data = float(max(p50.max(initial=0), p90.max(initial=0), p95.max(initial=0), p99.max(initial=0)))
    goal_ticks = 6
    step = _nice_step(ymax_data, goal_ticks=goal_ticks)

    HEADROOM_FRAC = 0.06   
    y_top_aligned = ceil(ymax_data / step) * step
    y_top = y_top_aligned + HEADROOM_FRAC * ymax_data
    y_top = min(y_top, ymax_data * 1.08)

    ax.set_ylim(0, y_top)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=goal_ticks, steps=[1, 2, 5, 10]))

    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)

    def _label_bars(rects):
        for rect in rects:
            h = rect.get_height()
            x_center = rect.get_x() + rect.get_width() / 2.0
            margin_out = 0.01 * ymax_data
            outside_y = h + margin_out
            if outside_y >= y_top * 0.98:
                ax.text(x_center, max(h - margin_out, 0.0),
                        _fmt_val(h), ha='center', va='top', rotation=0, clip_on=False)
            else:
                ax.text(x_center, outside_y,
                        _fmt_val(h), ha='center', va='bottom', rotation=0, clip_on=False)

    for group in (r1, r2, r3, r4):
        _label_bars(group)

    ax.legend(loc='upper right')
    fig.tight_layout()
    plt.savefig(out_pdf)
    plt.savefig(os.path.splitext(out_pdf)[0] + '.png', dpi=220)
    plt.close(fig)
    print(f"[ok] Saved: {out_pdf} and {os.path.splitext(out_pdf)[0] + '.png'}")

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

    out_pdf = os.path.join(out_root, f"probe_latency_{os.path.basename(d.rstrip(os.sep))}.pdf")
    title = f"{os.path.basename(d)}: Probe latency percentiles by batch"
    create_bar_chart(labels, p50_values, p90_values, p95_values, p99_values, out_pdf, title)

def parse_args():
    ap = argparse.ArgumentParser(
        description="Parse probe latency percentiles from logs and plot per-subdir bar charts."
    )
    ap.add_argument(
        "-i", "--input",
        type=str,
        default=".",
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
