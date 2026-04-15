import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import seaborn as sns

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import plot_common

# Unified color palette
palette = sns.color_palette("mako")

# Text sizes
TEXT_SIZE_XLABEL = 18
TEXT_SIZE_YLABEL = 18
TEXT_SIZE_XYAXIS = 18
TEXT_SIZE_LEGEND = 18

def parse_histogram_file(file_path):
    """Parse HistogramLogProcessor output file"""
    values = []
    percentiles = []
    inv_one_minus_p = []  # 1/(1-Percentile)
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
        # Skip header lines
        for line in lines[2:]:  # Skip first two lines (header)
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if len(parts) >= 4:
                try:
                    value = float(parts[0])          # in microseconds
                    percentile = float(parts[1])
                    inv_p_str = parts[3]
                    if inv_p_str.lower() == 'inf':
                        inv_p = float('inf')
                    else:
                        inv_p = float(inv_p_str)
                    values.append(value)
                    percentiles.append(percentile)
                    inv_one_minus_p.append(inv_p)
                except (ValueError, IndexError):
                    continue
    
    return np.array(values), np.array(percentiles), np.array(inv_one_minus_p)


def get_latency_at_percentile(values, percentiles, target_percentile):
    """
    Given arrays of latency values and corresponding percentiles,
    return the latency (in seconds) at the closest percentile >= target_percentile.
    """
    # Find the first index where percentile >= target
    idx = np.searchsorted(percentiles, target_percentile, side='left')
    if idx >= len(values):
        idx = len(values) - 1
    # Return value in seconds
    return values[idx] / 1_000_000.0


def plot_histogram_tail():
    """Plot adaptive subplot only"""
    # Parse data files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_vanilla_20ms = os.path.join(script_dir, 'vanilla_20ms.txt')
    file_vanilla_80ms = os.path.join(script_dir, 'vanilla_80ms.txt')
    file_xkernel_20ms = os.path.join(script_dir, 'xkernel_20ms.txt')
    file_xkernel_80ms = os.path.join(script_dir, 'xkernel_80ms.txt')
    
    # Parse adaptive files
    values_vanilla_20ms, percentiles_vanilla_20ms, inv_p_vanilla_20ms = parse_histogram_file(file_vanilla_20ms)
    values_vanilla_80ms, percentiles_vanilla_80ms, inv_p_vanilla_80ms = parse_histogram_file(file_vanilla_80ms)
    values_xkernel_20ms, percentiles_xkernel_20ms, inv_p_xkernel_20ms = parse_histogram_file(file_xkernel_20ms)
    values_xkernel_80ms, percentiles_xkernel_80ms, inv_p_xkernel_80ms = parse_histogram_file(file_xkernel_80ms)

    # --- Print P999 and P9999 latencies ---
    targets = {
        'P999': 0.999,
        'P9999': 0.9999
    }

    datasets = {
        'Vanilla (20ms)': (values_vanilla_20ms, percentiles_vanilla_20ms),
        'Vanilla (80ms)': (values_vanilla_80ms, percentiles_vanilla_80ms),
        'Adaptive SF (20ms)': (values_xkernel_20ms, percentiles_xkernel_20ms),
        'Adaptive SF (80ms)': (values_xkernel_80ms, percentiles_xkernel_80ms),
    }

    print("\n=== Tail Latency (FCT in seconds) ===")
    for name, (vals, pers) in datasets.items():
        print(f"\n{name}:")
        for label, p in targets.items():
            latency_sec = get_latency_at_percentile(vals, pers, p)
            print(f"  {label}: {latency_sec:.6f} s")

    # --- Plotting: apply masks for visualization only ---
    p9999_inv_p_max = 11000.0  # Allow up to slightly beyond 10,000 for p9999 (p99.99, two 9s)

    def apply_mask(values, percentiles, inv_p, max_inv_p):
        mask = np.isfinite(inv_p) & (inv_p <= max_inv_p)
        return inv_p[mask], values[mask] / 1_000.0  # convert to milliseconds
    
    # Adaptive data - up to p99.99 (two 9s)
    x_vanilla_20ms, y_vanilla_20ms = apply_mask(values_vanilla_20ms, percentiles_vanilla_20ms, inv_p_vanilla_20ms, p9999_inv_p_max)
    x_vanilla_80ms, y_vanilla_80ms = apply_mask(values_vanilla_80ms, percentiles_vanilla_80ms, inv_p_vanilla_80ms, p9999_inv_p_max)
    x_xkernel_20ms, y_xkernel_20ms = apply_mask(values_xkernel_20ms, percentiles_xkernel_20ms, inv_p_xkernel_20ms, p9999_inv_p_max)
    x_xkernel_80ms, y_xkernel_80ms = apply_mask(values_xkernel_80ms, percentiles_xkernel_80ms, inv_p_xkernel_80ms, p9999_inv_p_max)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(8, 3))
    
    # Set axes properties
    ax.set_xscale('log')
    ax.set_yscale('linear')
    ax.set_xlim([1.0, 11000.0])
    
    # Set y-axis max to 70
    y_max = 70
    ax.set_ylim([0, y_max])
    
    key_inv_p = [1.0, 10.0, 100.0, 1000.0, 10000.0]
    key_labels = ['0', 'p90', 'p99', 'p99.9', 'p99.99']
    ax.set_xticks(key_inv_p)
    ax.set_xticklabels(key_labels, fontsize=TEXT_SIZE_XYAXIS)
    
    # Set y-ticks: 0, 20, 40, 60 (not 70)
    y_ticks = [0, 20, 40, 60]
    ax.set_yticks(y_ticks)
    ax.tick_params(axis='both', labelsize=TEXT_SIZE_XYAXIS)
    
    # Plot data
    # Colors: SF=3 (light gray), XK (black)
    # Line styles: 20ms (dashed), 80ms (solid)
    # Line widths: XK (2), SF=3 (5)
    # No markers
    WIDTH=1.15
    line_objects = {}
    if len(x_vanilla_20ms) > 0 and len(y_vanilla_20ms) > 0:
        line, = ax.plot(x_vanilla_20ms, y_vanilla_20ms, 
                color='#B0B0B0', linewidth=4, label='SF=3 (20ms)', zorder=2, linestyle='-')
        line_objects['SF=3 (20ms)'] = line
    if len(x_xkernel_20ms) > 0 and len(y_xkernel_20ms) > 0:
        line, = ax.plot(x_xkernel_20ms, y_xkernel_20ms, 
                color='black', linestyle='-', linewidth=WIDTH, label='Adaptive SF (20ms)', zorder=2,
                marker='o', markersize=2.5, markeredgecolor='black', markerfacecolor='black', markevery=5)
        line_objects['Adaptive SF (20ms)'] = line
    if len(x_vanilla_80ms) > 0 and len(y_vanilla_80ms) > 0:
        line, = ax.plot(x_vanilla_80ms, y_vanilla_80ms, 
                color='#B0B0B0', linewidth=4, label='SF=3 (80ms)', zorder=2, linestyle='--')
        line_objects['SF=3 (80ms)'] = line
    if len(x_xkernel_80ms) > 0 and len(y_xkernel_80ms) > 0:
        line, = ax.plot(x_xkernel_80ms, y_xkernel_80ms, 
                color='black', linestyle='--', linewidth=WIDTH, label='Adaptive SF (80ms)', zorder=2,
                marker='o', markersize=2.5, markeredgecolor='black', markerfacecolor='black', markevery=5)
        line_objects['Adaptive SF (80ms)'] = line
    
    ax.set_xlabel('Percentile', fontsize=TEXT_SIZE_XLABEL)
    ax.set_ylabel('FCT (ms)', fontsize=TEXT_SIZE_YLABEL)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--', zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)
    
    # Create legend with custom handles
    # For SF=3 lines, create thinner handles for legend only
    from matplotlib.lines import Line2D
    ordered_labels = [
        'SF=3 (20ms)',
        'SF=3 (80ms)',
        'Adaptive SF (20ms)',
        'Adaptive SF (80ms)'
    ]
    
    all_handles = []
    all_labels = []
    for label in ordered_labels:
        if label in line_objects:
            original_line = line_objects[label]
            # For SF=3 lines, create a thinner handle for legend
            if label == 'SF=3 (20ms)':
                # Create a custom Line2D with thinner linewidth, normal length
                legend_handle = Line2D([0, 1], [0, 0], 
                                     color=original_line.get_color(),
                                     linestyle=original_line.get_linestyle(),
                                     linewidth=2.0,  # Thinner than actual line (4)
                                     label=label)
                all_handles.append(legend_handle)
            elif label.startswith('SF=3'):
                # SF=3 (80ms): thinner linewidth, slightly shorter
                legend_handle = Line2D([0, 0.92], [0, 0], 
                                     color=original_line.get_color(),
                                     linestyle=original_line.get_linestyle(),
                                     linewidth=2.0,
                                     label=label)
                all_handles.append(legend_handle)
            else:
                # For Adaptive SF, create slightly shorter handles
                legend_handle = Line2D([0, 0.92], [0, 0], 
                                     color=original_line.get_color(),
                                     linestyle=original_line.get_linestyle(),
                                     linewidth=original_line.get_linewidth(),
                                     marker=original_line.get_marker(),
                                     markersize=original_line.get_markersize(),
                                     markeredgecolor=original_line.get_markeredgecolor(),
                                     markerfacecolor=original_line.get_markerfacecolor(),
                                     label=label)
                all_handles.append(legend_handle)
            all_labels.append(label)
    
    # Create legend on ax to ensure correct style matching
    # Use handlelength to ensure all legend lines display fully
    ax.legend(all_handles, all_labels, loc='upper left', bbox_to_anchor=(0.005, 0.995), 
               ncol=1, frameon=False, fontsize=TEXT_SIZE_LEGEND, handlelength=1)
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plot_common.save_fig(script_dir, 'nginx_tail_adaptive')
    print(f"\nPlot saved to {script_dir}/nginx_tail_adaptive.pdf")
    
    plt.close()


if __name__ == '__main__':
    plot_histogram_tail()
