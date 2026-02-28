import re
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from plot_common import colors, markers

# Set font to use system default instead of Arial
plt.rcParams['font.family'] = 'DejaVu Sans'

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
    cdf_percent = np.arange(1, n + 1) / n * 100
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

# Configuration: set to True to show markers on the plot
SHOW_MARKERS = False

# 3. Plot both CDFs on the same figure
fig, ax = plt.subplots(figsize=(10, 6))

# Prepare plot arguments
plot_kwargs_klp = {'color': colors[0], 'linewidth': 2, 'label': 'Linux KLP'}
plot_kwargs_xk = {'color': colors[1], 'linewidth': 2, 'label': 'Xkernel'}

# Add markers if enabled
if SHOW_MARKERS:
    plot_kwargs_klp['marker'] = markers[0]
    plot_kwargs_klp['markersize'] = 6
    plot_kwargs_xk['marker'] = markers[1]
    plot_kwargs_xk['markersize'] = 6

ax.plot(linux_klp_sorted, linux_klp_cdf, **plot_kwargs_klp)
ax.plot(xkernel_sorted, xkernel_cdf, **plot_kwargs_xk)
ax.set_xscale('log')
ax.set_xlabel('Transition Delay (μs, log scale)', fontsize='x-large')
ax.set_ylabel('CDF (%)', fontsize='x-large')
ax.grid(True, alpha=0.3)
ax.set_ylim([0, 100])
ax.legend(loc='best', fontsize='large')

plt.tight_layout()
plt.savefig("per_task_cdf.pdf", dpi=500, bbox_inches='tight')
plt.close()