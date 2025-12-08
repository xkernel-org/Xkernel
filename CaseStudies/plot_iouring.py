import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Data from the screenshots
# Left side: value=20, Right side: value=10
latency_metrics = ['p50', 'Avg.', 'p90', 'p99', 'p99.9', 'p99.99']
value_20 = [13.79, 14.23, 16.25, 19.34, 28.47, 90.92]  # Left screenshot
value_10 = [13.29, 13.69, 15.53, 18.52, 22.21, 48.25]  # Right screenshot

throughput_20 = 35015.41  # Left screenshot
throughput_10 = 36477.05  # Right screenshot

# Create figure with two subplots with different widths
fig = plt.figure(figsize=(10, 4))
# Use gridspec to control width ratios - left plot wider, right plot narrower
gs = fig.add_gridspec(1, 2, width_ratios=[6, 1], wspace=0.15)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

# === Left subplot: Latency ===
x = np.arange(len(latency_metrics))
width = 0.35  # Thinner bars

# Use plot_common colors with hatching pattern
bars1 = ax1.bar(x - width/2, value_20, width, label='value=20', 
                color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=3)
bars2 = ax1.bar(x + width/2, value_10, width, label='value=10', 
                color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=3)

ax1.set_ylabel('Latency (us)')
ax1.set_xticks(x)
ax1.set_xticklabels(latency_metrics, rotation=0, ha='center')
ax1.tick_params(axis='x', length=0)
ax1.set_ylim(0, 100)
ax1.legend(frameon=True, facecolor='white', framealpha=1.0, fontsize=20)
# Remove bounding box, keep only left and bottom spines
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
# Make axis lines thicker
ax1.spines['left'].set_linewidth(1)
ax1.spines['bottom'].set_linewidth(1)

# === Right subplot: Throughput ===
throughput_metrics = ['Tpt.']
x2 = np.arange(len(throughput_metrics))

bars3 = ax2.bar(x2 - width/2, [throughput_20], width, label='value=20', 
                color=plot_common.colors[2], edgecolor='black', linewidth=1, zorder=3)
bars4 = ax2.bar(x2 + width/2, [throughput_10], width, label='value=10', 
                color=plot_common.colors[4], edgecolor='black', linewidth=1, zorder=3)

ax2.set_xticks(x2)
ax2.set_xticklabels(throughput_metrics)
ax2.tick_params(axis='x', length=0)
ax2.set_ylim(0, 38000)
ax2.set_yticks([0, 10000, 20000, 30000])
ax2.set_yticklabels(['0', '10K', '20K', '30K'])
ax2.set_xlim(-0.6, 0.6)  # Tighten x-axis limits around the bars
# Add IOPS text above 30K, aligned with y-labels
ax2.text(-0.75, 33200, 'IOPS', ha='right', va='bottom', fontsize=20)
# Remove bounding box, keep only left and bottom spines
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
# Make axis lines thicker
ax2.spines['left'].set_linewidth(1)
ax2.spines['bottom'].set_linewidth(1)

# Adjust layout and save
plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'iouring')
plt.close()
