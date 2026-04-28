import glob
import re
import os
import matplotlib.pyplot as plt
import numpy as np
import sys
import seaborn as sns
from matplotlib.ticker import LogLocator

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import plot_common

# Unified color palette
palette = sns.color_palette("mako")

# Text sizes
TEXT_SIZE_XYLABEL = 18
TEXT_SIZE_XYAXIS = 18
TEXT_SIZE_LEGEND = 16

# Tick parameters
TICK_LENGTH_X = 5
TICK_WIDTH_X = 1 

def apply_academic_style(ax):
    """Apply academic plot styling with log-scale settings."""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)
    
    # Set the y-axis to log scale
    ax.set_yscale('log')
    
    # [Change 1] Show only major grid lines to avoid too many dashed lines.
    # This used to be 'both'; it is now 'major'.
    
    ax.tick_params(width=2.5, length=6, which='major', labelsize=TEXT_SIZE_XYAXIS)
    ax.tick_params(width=1.5, length=4, which='minor')

def parse_and_plot_styled():
    # --- 2. Data parsing ---
    files = glob.glob('L*-*.txt')
    data_map = {}
    all_l_values = set()
    all_threads = set()

    print(f"Found {len(files)} files. Processing...")

    for filepath in files:
        try:
            filename = os.path.basename(filepath)
            nums = re.findall(r'\d+', filename)
            if len(nums) < 2: continue
            
            l_val = int(nums[0])
            l_val -= 7 # Preserve the existing offset logic
            thread_num = int(nums[1])
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                time_match = re.search(r'time:\s*(\d+)\s*us', content)
                op_match = re.search(r'op count:\s*(\d+)', content)
                
                if time_match:
                    time_val = int(time_match.group(1))
                    op_val = int(op_match.group(1)) if op_match else 0
                    
                    if thread_num not in data_map: data_map[thread_num] = {}
                    data_map[thread_num][l_val] = {'time': time_val, 'ops': op_val}
                    all_l_values.add(l_val)
                    all_threads.add(thread_num)
        except Exception:
            continue

    if not data_map:
        print("No valid data")
        return

    # --- 3. Plotting logic ---
    sorted_threads = sorted(list(all_threads))
    sorted_l_keys = sorted(list(all_l_values))
    
    x_indexes = np.arange(len(sorted_threads))
    total_width = 0.8
    bar_width = total_width / len(sorted_l_keys)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3), sharey=False)

    colors = [palette[2], palette[4], palette[1], palette[0]]

    for i, l_val in enumerate(sorted_l_keys):
        offset = (i - len(sorted_l_keys)/2) * bar_width + bar_width/2
        current_color = colors[i % len(colors)]
        
        y_times = []
        y_ops = []
        for t in sorted_threads:
            data = data_map.get(t, {}).get(l_val, {'time': 0, 'ops': 0})
            y_times.append(data['time'] / 1000.0)  # Convert from us to ms
            y_ops.append(data['ops'])
        
        # [Change 2] Draw bar charts and keep returned rects for value labels
        rects1 = ax1.bar(x_indexes + offset, y_times, width=bar_width, 
                         label=f'$L$={l_val}', 
                         color=current_color, zorder=2)
        
        rects2 = ax2.bar(x_indexes + offset, y_ops, width=bar_width, 
                         color=current_color, zorder=2)

        # Add numeric labels (fontsize=16 avoids oversized labels; fmt='%d' keeps integers)
        # padding=3 places text slightly above the bars
        # ax1.bar_label(rects1, fmt='%d', label_type='edge', fontsize=16, padding=3)
        # ax2.bar_label(rects2, fmt='%d', label_type='edge', fontsize=16, padding=3)

    # --- 4. Style and layout adjustments ---
    
    # Configure Axis 1
    ax1.set_ylabel('Delay (ms)', fontsize=TEXT_SIZE_XYLABEL)
    apply_academic_style(ax1)
    ax1.set_xticks(x_indexes)
    ax1.set_xlabel('# of Threads', fontsize=TEXT_SIZE_XYLABEL)
    ax1.set_xticklabels(sorted_threads, fontsize=TEXT_SIZE_XYAXIS)
    ax1.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)
    ax1.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)
    
    # Increase numticks to 100 to force minor ticks to display
    ax1.yaxis.set_minor_locator(LogLocator(base=10, subs=[2, 5], numticks=100))
    
    ax1.tick_params(axis='y', which='minor', length=4, width=1.5, left=True)
    # Configure Axis 2
    ax2.set_ylabel('# of RefCnt Access', fontsize=TEXT_SIZE_XYLABEL)
    ax2.set_xlabel('# of Threads', fontsize=TEXT_SIZE_XYLABEL)
    ax2.set_xticks(x_indexes)
    ax2.set_xticklabels(sorted_threads, fontsize=TEXT_SIZE_XYAXIS)
    apply_academic_style(ax2)
    ax2.tick_params(axis='x', length=TICK_LENGTH_X, width=TICK_WIDTH_X, labelsize=TEXT_SIZE_XYAXIS)
    ax2.tick_params(axis='y', labelsize=TEXT_SIZE_XYAXIS)

    ax2.yaxis.set_minor_locator(LogLocator(base=10, subs=[2, 5], numticks=100))
    ax2.tick_params(axis='y', which='minor', length=4, width=1.5, left=True)

    # Legend settings: place it in the upper-left corner of the first plot
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles, labels, 
               loc='upper left', 
               frameon=False, fontsize=TEXT_SIZE_LEGEND)

    plt.subplots_adjust(wspace=0.3)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plot_common.save_fig(script_dir, 'global_converge')
    plt.close()

if __name__ == "__main__":
    parse_and_plot_styled()
