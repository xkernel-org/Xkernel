import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter, LogFormatterSciNotation
import os
import sys
import seaborn as sns

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Unified color palette
palette = sns.color_palette("mako")

# Text sizes
TEXT_SIZE_XYLABEL = 20
TEXT_SIZE_XYAXIS = 20
TEXT_SIZE_LEGEND = 20

def parse_func_instr_size_data(file_path):
    """Parse function instruction size data from file"""
    data = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Split by comma and convert each value to int
        values = [int(x.strip()) for x in line.split(',')]
        data.extend(values)
    
    return np.array(data)

def parse_cs_instr_size_data(file_path):
    """Parse CS instruction size data from file"""
    data = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Each line contains a single integer
        data.append(int(line))
    
    return np.array(data)

def calculate_cdf(data):
    """Calculate CDF for given data"""
    data_sorted = np.sort(data)
    n = len(data_sorted)
    cdf_percent = np.arange(1, n + 1) / n
    return data_sorted, cdf_percent

# 1. Read and parse data from all files
data_dir = os.path.dirname(os.path.abspath(__file__))
func_file = os.path.join(data_dir, 'func_instr_size.txt')
cs_file = os.path.join(data_dir, 'cs_instr_size.txt')
ss_file = os.path.join(data_dir, 'ss_instr_size.txt')

func_data = parse_func_instr_size_data(func_file)
cs_data = parse_cs_instr_size_data(cs_file)
ss_data = parse_cs_instr_size_data(ss_file)

# 2. Calculate CDF for all datasets
func_sorted, func_cdf = calculate_cdf(func_data)
cs_sorted, cs_cdf = calculate_cdf(cs_data)
ss_sorted, ss_cdf = calculate_cdf(ss_data)

# 3. Plot all CDFs on the same figure
fig, ax = plt.subplots(figsize=(8, 2.95))

ax.plot(cs_sorted, cs_cdf * 100, color=palette[4], linewidth=2.5, label='CSes', zorder=2)
ax.plot(ss_sorted, ss_cdf * 100, color=palette[2], linewidth=2.5, label='SSes', zorder=2)
ax.plot(func_sorted, func_cdf * 100, color=palette[0], linewidth=2.5, label='Functions', zorder=2)

ax.set_xscale('log')
# Custom formatter for x-axis: show 10^0 as 1
def x_formatter(x, pos):
    if x == 1:
        return '1'
    return f'$10^{{{int(np.log10(x))}}}$'
ax.xaxis.set_major_formatter(FuncFormatter(x_formatter))
ax.set_xlabel('# of instructions', fontsize=TEXT_SIZE_XYLABEL)
ax.set_ylabel('CDF (%)', fontsize=TEXT_SIZE_XYLABEL)
ax.tick_params(axis='x', length=10, width=2, labelsize=TEXT_SIZE_XYAXIS)
ax.tick_params(axis='y', length=10, width=2, labelsize=TEXT_SIZE_XYAXIS)
ax.grid(True, alpha=0.3, zorder=0)
ax.set_ylim(0, 100)
ax.set_yticks(np.arange(0, 101, 25))
# Format y-axis: show as integers with % sign
def y_formatter(x, pos):
    return f'{int(x)}'
ax.yaxis.set_major_formatter(FuncFormatter(y_formatter))
ax.legend(loc='best', frameon=False, fontsize=TEXT_SIZE_LEGEND)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
# Make axis lines thicker
ax.spines['left'].set_linewidth(1)
ax.spines['bottom'].set_linewidth(1)

plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'instr_compare')
plt.close()

