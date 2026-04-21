#!/usr/bin/env python3
"""
Figure 16 — kprobe trigger overhead (slowdown vs offered IOPS).

Reads benchmark output from data/ directory:
  base_<delay>_<iops>.txt    — no kprobe (baseline)
  xk_<delay>_<iops>.txt      — jump-optimized kprobe [OPTIMIZED]
  xkint3_<delay>_<iops>.txt  — INT3 kprobe (optimization disabled)

Plots P50 latency slowdown (%) as a function of offered IOPS.
"""

import os
import re
import sys

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from matplotlib.ticker import FuncFormatter, FixedLocator
import seaborn as sns

# Import shared styling
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_common

# ── Style constants ──────────────────────────────────────────────────
palette = sns.color_palette("mako")

TEXT_SIZE_XYLABEL  = 17
TEXT_SIZE_XYAXIS   = 17
TEXT_SIZE_ANNOTATE = 14
TEXT_SIZE_LEGEND   = 17


def apply_paper_style(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)
    ax.tick_params(axis='both', which='major', length=10, width=2)
    ax.grid(True, alpha=0.3, zorder=0, linestyle='--')


def iops_formatter(x, pos):
    if x < 1_000_000 and x > 0:
        return f'{x / 1_000_000:.1f}'
    return f'{int(x / 1_000_000)}'


def percent_formatter(x, pos):
    if x == 0:
        return ''
    return f'{int(x * 100)}%'


# ── Data reading ─────────────────────────────────────────────────────
def read_cases_data(file_path):
    """Read annotated case data from cases.txt (optional).
    Format: IOPS/s, slowdown%
    """
    cases = []
    if not os.path.exists(file_path):
        return cases
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) != 2:
                continue
            try:
                iops = int(parts[0].strip().replace('/s', '').replace(',', ''))
                sd   = float(parts[1].strip().replace('%', '')) / 100.0
                cases.append((iops, sd))
            except ValueError:
                continue
    return cases


# ── Main ─────────────────────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
figure_dir = os.path.dirname(script_dir)

# Allow passing data directory as argument (default: ../data)
if len(sys.argv) > 1:
    data_dir = sys.argv[1]
else:
    data_dir = os.path.join(figure_dir, 'data')

cases_file = os.path.join(figure_dir, 'cases.txt')
cases_data = read_cases_data(cases_file)

start_iops = 100_000
end_iops   = 10_000_000
step       = 100_000

# Auto-detect delay values from filenames
filename_re = re.compile(r'(?:base|xk|xkint3)_(\d+)_(\d+)\.txt')
detected_delays = set()

print(f"Scanning: {data_dir}")
if os.path.isdir(data_dir):
    for fn in os.listdir(data_dir):
        m = filename_re.match(fn)
        if m:
            detected_delays.add(int(m.group(1)))

sorted_delays = sorted(detected_delays)
print(f"Detected delays: {sorted_delays} us")

if not sorted_delays:
    print("No data files found.")
    sys.exit(1)

# ── Parse results and compute slowdown ───────────────────────────────
plot_data_map       = {}   # delay → {iops, slowdown_p50, slowdown_p99}
plot_data_map_xkint3 = {}

for delay in sorted_delays:
    print(f"Processing delay={delay}us ...")
    raw = {
        prefix: {'p50': {}, 'p99': {}}
        for prefix in ('base', 'xk', 'xkint3')
    }

    for prefix in raw:
        for iops in range(start_iops, end_iops + 1, step):
            fpath = os.path.join(data_dir, f"{prefix}_{delay}_{iops}.txt")
            if not os.path.exists(fpath):
                continue
            with open(fpath) as f:
                content = f.read()
            m50 = re.search(r'P50[:\s]+(\d+)', content, re.IGNORECASE)
            m99 = re.search(r'P99[:\s]+(\d+)', content, re.IGNORECASE)
            if m50:
                raw[prefix]['p50'][iops] = int(m50.group(1))
            if m99:
                raw[prefix]['p99'][iops] = int(m99.group(1))

    # xk vs base
    common = sorted(set(raw['base']['p50']) & set(raw['xk']['p50'])
                    & set(raw['base']['p99']) & set(raw['xk']['p99']))
    cur = {'iops': [], 'slowdown_p50': [], 'slowdown_p99': []}
    for iops in common:
        bp50, xp50 = raw['base']['p50'][iops], raw['xk']['p50'][iops]
        bp99, xp99 = raw['base']['p99'][iops], raw['xk']['p99'][iops]
        if bp50 > 0 and bp99 > 0:
            cur['iops'].append(iops)
            cur['slowdown_p50'].append((xp50 - bp50) / bp50)
            cur['slowdown_p99'].append((xp99 - bp99) / bp99)
    if cur['iops']:
        plot_data_map[delay] = cur

    # xkint3 vs base
    common3 = sorted(set(raw['base']['p50']) & set(raw['xkint3']['p50'])
                     & set(raw['base']['p99']) & set(raw['xkint3']['p99']))
    cur3 = {'iops': [], 'slowdown_p50': [], 'slowdown_p99': []}
    for iops in common3:
        bp50, ip50 = raw['base']['p50'][iops], raw['xkint3']['p50'][iops]
        bp99, ip99 = raw['base']['p99'][iops], raw['xkint3']['p99'][iops]
        if bp50 > 0 and bp99 > 0:
            cur3['iops'].append(iops)
            cur3['slowdown_p50'].append((ip50 - bp50) / bp50)
            cur3['slowdown_p99'].append((ip99 - bp99) / bp99)
    if cur3['iops']:
        plot_data_map_xkint3[delay] = cur3

if not plot_data_map:
    print("No matching base/xk data pairs found.")
    sys.exit(1)

# ── Summary table ────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"  {'Delay (µs)':<12} {'IOPS Points':>12}  {'P50 Slowdown':>14}  {'P99 Slowdown':>14}")
print("-" * 62)
for delay in sorted_delays:
    if delay not in plot_data_map:
        continue
    d = plot_data_map[delay]
    n = len(d['iops'])
    avg_p50 = np.mean(d['slowdown_p50']) * 100
    max_p50 = max(d['slowdown_p50']) * 100
    avg_p99 = np.mean(d['slowdown_p99']) * 100
    max_p99 = max(d['slowdown_p99']) * 100
    print(f"  {delay:<12} {n:>12}  {f'avg {avg_p50:.1f}%':>14}  {f'avg {avg_p99:.1f}%':>14}")
print("-" * 62)
all_p50 = []
for d in plot_data_map.values():
    all_p50.extend(d['slowdown_p50'])
print(f"  {'Overall':<12} {'':>12}  {f'avg {np.mean(all_p50)*100:.1f}%':>14}")
print("=" * 62)

# ── Plot ─────────────────────────────────────────────────────────────
colors = [palette[4], palette[3], palette[2], palette[0]]
fig, ax = plt.subplots(figsize=(8, 3.5))

line_width   = 2
marker_size  = 2

for idx, delay in enumerate(sorted_delays):
    if delay not in plot_data_map:
        continue
    data  = plot_data_map[delay]
    color = '#8F0177' if idx == 0 else colors[idx % len(colors)]

    ax.plot(data['iops'], data['slowdown_p50'],
            color=color, linestyle='--', linewidth=line_width,
            marker='o', markersize=marker_size, markevery=1,
            label=f'{delay}µs')

# (optional) xkint3 overlay — uncomment to show INT3 comparison
# for delay in sorted_delays:
#     if delay not in plot_data_map_xkint3:
#         continue
#     data = plot_data_map_xkint3[delay]
#     ax.plot(data['iops'], data['slowdown_p50'],
#             color='orange', linestyle=':', linewidth=line_width,
#             marker='o', markersize=marker_size, markevery=1,
#             label=f'{delay}µs (INT3)', zorder=5)

# ── Styling ──────────────────────────────────────────────────────────
apply_paper_style(ax)

ax.set_xlabel(r'Offered IOPS ($\times10^6$/s)', fontsize=TEXT_SIZE_XYLABEL)
ax.set_ylabel('Slowdown (%)', fontsize=TEXT_SIZE_XYLABEL)

ax.set_ylim(0, 0.20)
y_ticks = [0, 0.01, 0.05, 0.10, 0.15, 0.20]
ax.yaxis.set_major_locator(FixedLocator(y_ticks))
ax.yaxis.set_major_formatter(FuncFormatter(percent_formatter))
ax.axhline(y=0, color='black', linestyle=':', linewidth=2, alpha=0.8, zorder=1)

ax.xaxis.set_major_formatter(FuncFormatter(iops_formatter))

all_iops = []
for d in plot_data_map.values():
    all_iops.extend(d['iops'])

if all_iops:
    min_iops, max_iops = min(all_iops), max(all_iops)
    tick_step = 1_000_000
    if (max_iops - min_iops) < 2_000_000:
        tick_step = 200_000
    elif (max_iops - min_iops) > 15_000_000:
        tick_step = 2_000_000

    start_tick   = (min_iops // tick_step) * tick_step
    major_ticks  = [t for t in np.arange(start_tick, max_iops + tick_step, tick_step)
                    if t >= min_iops - tick_step / 2]
    ax.set_xticks(major_ticks)
    ax.set_xlim(min_iops, max_iops)

    if min_iops < 1_000_000:
        minor = [t for t in np.arange(0, 1_000_001, 100_000)
                 if 0 <= t <= max_iops]
        ax.set_xticks(minor, minor=True)
        ax.tick_params(axis='x', which='minor', labelbottom=False,
                       length=4, width=1, color='gray')

ax.tick_params(axis='x', labelsize=TEXT_SIZE_XYAXIS)
ax.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)

# Annotated case markers (from cases.txt)
if cases_data:
    ax.scatter([c[0] for c in cases_data],
               [c[1] for c in cases_data],
               marker='^', s=100, color=sns.color_palette("rocket")[2],
               linewidths=2, zorder=10, label='Cases')

legend = ax.legend(loc='lower center', bbox_to_anchor=(0.45, 1.02),
                   ncol=6, frameon=False, fontsize=TEXT_SIZE_LEGEND,
                   handlelength=1.2)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plot_common.save_fig(script_dir, 'figure16')
plt.close()
print(f"Saved: {script_dir}/figure16.pdf")
