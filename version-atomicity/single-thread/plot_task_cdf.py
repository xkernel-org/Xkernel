import re
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
import os
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import plot_common

def parse_linux_klp_data(file_path):
    """Parse Linux KLP data from file"""
    with open(file_path, 'r') as f:
        raw_data = f.read()
    
    waited_ns = []
    lines = raw_data.strip().split('\n')
    for line in lines:
        # Match format: [Success!] ... | Waited: XXX ns | ...
        match = re.search(r'Waited: (\d+) ns', line)
        if match:
            waited_ns.append(int(match.group(1)))
    
    # Convert to microseconds
    waited_us = np.array([x / 1000.0 for x in waited_ns])
    return waited_us

def parse_xkernel_data(file_path):
    """Parse Xkernel data from file"""
    with open(file_path, 'r') as f:
        raw_data = f.read()
    
    waited_us = []
    lines = raw_data.strip().split('\n')
    for line in lines:
        match = re.search(r'差值：(\d+) us', line)
        if match:
            waited_us.append(int(match.group(1)))
    
    return np.array(waited_us)

def calculate_cdf(data):
    """Calculate CDF for given data"""
    data_sorted = np.sort(data)
    n = len(data_sorted)
    cdf_percent = np.arange(1, n + 1) / n
    return data_sorted, cdf_percent

# 1. Read and parse data from both files
data_dir = os.path.dirname(os.path.abspath(__file__))
linux_klp_file = os.path.join(data_dir, 'per_task_data.txt')
xkernel_file = os.path.join(data_dir, 'per_task_data_xk.txt')

linux_klp_data = parse_linux_klp_data(linux_klp_file)
xkernel_data = parse_xkernel_data(xkernel_file)

# 2. Calculate CDF for both datasets
linux_klp_sorted, linux_klp_cdf = calculate_cdf(linux_klp_data)
xkernel_sorted, xkernel_cdf = calculate_cdf(xkernel_data)

# 3. Plot both CDFs on the same figure
fig, ax = plt.subplots(figsize=(8, 4))

ax.plot(linux_klp_sorted, linux_klp_cdf, color=plot_common.colors[2], linewidth=2, label='Linux KLP', 
        marker=plot_common.markers[0], markersize=2, zorder=2)
ax.plot(xkernel_sorted, xkernel_cdf, color=plot_common.colors[4], linewidth=2, label='Xkernel',
        marker=plot_common.markers[2], markersize=2, zorder=2)

ax.set_xscale('log')
ax.set_xlabel('Transition Delay (μs)')
ax.set_ylabel('CDF (%)')
ax.tick_params(axis='x', length=10, width=2)
ax.tick_params(axis='y', length=10, width=2)
ax.grid(True, alpha=0.3, zorder=0)
ax.set_ylim(0, 1)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
# Format y-axis as percentage
def y_formatter(x, pos):
    return f'{int(x * 100)}'
ax.yaxis.set_major_formatter(FuncFormatter(y_formatter))
ax.legend(loc='best', frameon=True, facecolor='white', framealpha=1.0, fontsize=20)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
# Make axis lines thicker
ax.spines['left'].set_linewidth(1)
ax.spines['bottom'].set_linewidth(1)

plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'per_task_cdf')
plt.close()