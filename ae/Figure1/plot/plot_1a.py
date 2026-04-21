#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot Figure 1(a): FIO throughput on HDD (V=32 vs V=128)."""
import re
import sys
import os
import warnings
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

TEXT_SIZE = 18
TEXT_SIZE_XYLABEL = 20
TEXT_SIZE_XYAXIS = 20
TEXT_SIZE_LEGEND = 20
TICK_LENGTH_X = 5
TICK_WIDTH_X = 1

palette = sns.color_palette("mako")
COLOR_128 = palette[2]
COLOR_32 = palette[3]

script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'results')


def parse_hdd_log(path):
    """Extract BW (MiB/s) from fio_bench summary log."""
    with open(path) as f:
        for line in f:
            m = re.match(r'\s*BW\s*:\s*([\d.]+)\s*MiB/s', line)
            if m:
                return float(m.group(1))
    return 0


try:
    t_32_read  = parse_hdd_log(os.path.join(results_dir, 'hdd_32_read.txt'))
    t_128_read = parse_hdd_log(os.path.join(results_dir, 'hdd_128_read.txt'))
    t_32_write  = parse_hdd_log(os.path.join(results_dir, 'hdd_32_write.txt'))
    t_128_write = parse_hdd_log(os.path.join(results_dir, 'hdd_128_write.txt'))
except FileNotFoundError as e:
    print(f"Warning: HDD log not found ({e}). Using dummy data.", file=sys.stderr)
    t_32_read, t_128_read = 28.1, 201
    t_32_write, t_128_write = 3.8, 205

tp_values_32 = [t_32_read, t_32_write]
tp_values_128 = [t_128_read, t_128_write]
tp_labels = ['Read', 'Write']

# ── Plot ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(4, 3.5))

common_width = 0.18
group_spacing = 0.45
x_tp = np.array([0, group_spacing])

rects1 = ax.bar(x_tp - common_width/2, tp_values_32, common_width,
                label='32', color=COLOR_32, zorder=2)
rects2 = ax.bar(x_tp + common_width/2, tp_values_128, common_width,
                label='128', color=COLOR_128, zorder=2)

ax.set_ylabel('Tput. (MB/s)', fontsize=TEXT_SIZE_XYLABEL)
ax.set_xticks(x_tp)
ax.set_xticklabels(tp_labels, fontsize=TEXT_SIZE_XYAXIS)
ax.set_yticks([0, 100, 200])
ax.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
ax.set_ylim(0, 250)
ax.set_xlim(-0.3, group_spacing + 0.3)
ax.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

for rect in rects1 + rects2:
    height = rect.get_height()
    ax.text(rect.get_x() + rect.get_width()/2, height + 2,
            f'{height}', ha='center', va='bottom', fontsize=TEXT_SIZE, rotation=90)

ax.legend(loc='upper left', ncol=2, frameon=False, fontsize=TEXT_SIZE_LEGEND)

plt.tight_layout()
plot_common.save_fig(script_dir, 'figure1a')
plt.close(fig)

# ── Print summary table (matches README Expected Results) ────────────
read_improv = (t_128_read / t_32_read - 1) * 100 if t_32_read else 0
write_improv = (t_128_write / t_32_write - 1) * 100 if t_32_write else 0

print()
print("=" * 62)
print("  Figure 1(a) — FIO Throughput on HDD (BLK_MAX_REQUEST_COUNT)")
print("=" * 62)
print(f"  {'Workload':<12} {'V=32':>12} {'V=128':>12} {'Improvement':>14}")
print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*14}")
print(f"  {'Read':<12} {t_32_read:>9.2f} MB/s {t_128_read:>9.2f} MB/s {read_improv:>+11.0f}%")
print(f"  {'Write':<12} {t_32_write:>9.2f} MB/s {t_128_write:>9.2f} MB/s {write_improv:>+11.0f}%")
print("=" * 62)
