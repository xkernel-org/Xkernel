#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot fio throughput bar chart from results/ log files.

Expected files in ../results/:
  hdd_32_read.log, hdd_128_read.log, hdd_32_write.log, hdd_128_write.log
"""
import matplotlib.pyplot as plt
import numpy as np
import os
import re
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'results')


def parse_log(path):
    """Extract BW (MiB/s), IOPS, p50, p90 from a fio_bench summary log."""
    data = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            m = re.match(r'BW\s*:\s*([\d.]+)\s*MiB/s', line)
            if m:
                data['bw'] = float(m.group(1))
            m = re.match(r'IOPS\s*:\s*([\d,]+)', line)
            if m:
                data['iops'] = int(m.group(1).replace(',', ''))
            m = re.match(r'p50 clat\s*:\s*([\d.]+)\s*(\S+)', line)
            if m:
                data['p50'] = float(m.group(1))
                data['p50_unit'] = m.group(2)
            m = re.match(r'p90 clat\s*:\s*([\d.]+)\s*(\S+)', line)
            if m:
                data['p90'] = float(m.group(1))
                data['p90_unit'] = m.group(2)
    return data


# Read results
log_files = {
    'read_32':  os.path.join(results_dir, 'hdd_32_read.log'),
    'read_128': os.path.join(results_dir, 'hdd_128_read.log'),
    'write_32': os.path.join(results_dir, 'hdd_32_write.log'),
    'write_128': os.path.join(results_dir, 'hdd_128_write.log'),
}

results = {}
for key, path in log_files.items():
    if not os.path.exists(path):
        print(f"WARNING: {path} not found, skipping", file=sys.stderr)
        continue
    results[key] = parse_log(path)

# Extract throughput values (MiB/s)
read_32_tpt  = results.get('read_32',  {}).get('bw', 0)
read_128_tpt = results.get('read_128', {}).get('bw', 0)
write_32_tpt  = results.get('write_32',  {}).get('bw', 0)
write_128_tpt = results.get('write_128', {}).get('bw', 0)

# Create bar chart
fig, ax = plt.subplots(1, 1, figsize=(6, 4))
categories = ['Read', 'Write']
x = np.array([0, 0.6])
width = 0.2
spacing = width

bars_read_32 = ax.bar(x[0] - spacing/2, [read_32_tpt], width, label='value=32',
                      color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
bars_read_128 = ax.bar(x[0] + spacing/2, [read_128_tpt], width, label='value=128',
                       color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)
bars_write_32 = ax.bar(x[1] - spacing/2, [write_32_tpt], width,
                       color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=2)
bars_write_128 = ax.bar(x[1] + spacing/2, [write_128_tpt], width,
                        color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=2)

ax.set_ylabel('Throughput (MiB/s)')
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.tick_params(axis='x', length=0)

max_val = max(read_32_tpt, read_128_tpt, write_32_tpt, write_128_tpt)
ax.set_yticks(np.arange(0, int(max_val * 1.3) + 1, max(50, int(max_val / 3 / 50) * 50)))
ax.legend(loc='upper left', ncol=2, frameon=True, facecolor='white', framealpha=1.0)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1)
ax.spines['bottom'].set_linewidth(1)

# Add value labels on bars
for bars, values in [(bars_read_32, [read_32_tpt]), (bars_read_128, [read_128_tpt]),
                     (bars_write_32, [write_32_tpt]), (bars_write_128, [write_128_tpt])]:
    for bar, value in zip(bars, values):
        height = bar.get_height()
        x_pos = bar.get_x() + bar.get_width() / 2.0
        fmt = f'{value:.1f}' if value < 10 else f'{value:.0f}'
        ax.text(x_pos, height + 2, fmt, ha='center', va='bottom', fontsize=20)

plt.tight_layout()
plot_common.save_fig(script_dir, 'fio_tpt')
plt.close(fig)
