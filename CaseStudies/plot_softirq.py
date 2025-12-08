import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Read the CSV file
df = pd.read_csv('softirq.csv')

# Filter rows where MAX_SOFTIRQ_TIME is 2ms
df_filtered = df[df['MAX_SOFTIRQ_TIME'] == '2ms']

# Create figure and primary axis
fig, ax1 = plt.subplots(figsize=(6, 4))

# Plot worst latency on left y-axis
color1 = plot_common.colors[0]
ax1.set_xlabel('MAX_SOFTIRQ_RESTART', color='black')
ax1.set_ylabel('Worst Latency (us)', color='black')
ax1.plot(df_filtered['MAX_SOFTIRQ_RESTART'], df_filtered['WorstLatUs'], 
         marker=plot_common.markers[0], color=color1, linewidth=2, markersize=10, label='Worst Latency')
ax1.tick_params(axis='y', labelcolor='black')
ax1.tick_params(axis='x', labelcolor='black')

# Set y-axis limits for left axis (start at 0)
ax1.set_ylim(bottom=0)

# Set x-axis ticks to show only 1, 5, 10, 15, 20
ax1.set_xticks([1, 5, 10, 15, 20])

# Add vertical line at x = 10 (black)
ax1.axvline(x=10, color='black', linestyle='--', linewidth=2, alpha=0.7)
ax1.text(9.4, ax1.get_ylim()[1] * 0.95, 'Default Value', ha='center', va='top', color='black', fontsize=20)

# Create secondary y-axis for CPU utilization
ax2 = ax1.twinx()
color2 = plot_common.colors[2]
ax2.set_ylabel('CPU Usage (%)', color='black')
ax2.plot(df_filtered['MAX_SOFTIRQ_RESTART'], df_filtered['CpuUtilPct'], 
         marker=plot_common.markers[2], color=color2, linewidth=2, markersize=10, label='CPU Usage')
ax2.tick_params(axis='y', labelcolor='black')

# Set y-axis limits for right axis (0 to 100%)
ax2.set_ylim(0, 100)

# Remove top and right spines, set spine colors to black
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_color('black')
ax1.spines['bottom'].set_color('black')
ax2.spines['top'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.spines['right'].set_color('black')
ax2.spines['bottom'].set_color('black')

# Adjust layout and save
fig.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'softirq')
plt.close()
