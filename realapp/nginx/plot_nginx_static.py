import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import plot_common

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
                    value = float(parts[0])
                    percentile = float(parts[1])
                    # Parse 1/(1-Percentile) - handle "inf" case
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


def plot_histogram_tail():
    """Plot HistogramLogProcessor style tail latency chart"""
    # Parse data files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_vanilla_20ms = os.path.join(script_dir, 'w3_20ms_sf3.txt')
    file_vanilla_80ms = os.path.join(script_dir, 'w3_80ms_sf3.txt')
    file_xkernel_20ms = os.path.join(script_dir, 'w3_20ms_sf1.txt')
    file_xkernel_80ms = os.path.join(script_dir, 'w3_80ms_sf1.txt')
    
    # Parse all files
    values_vanilla_20ms, percentiles_vanilla_20ms, inv_p_vanilla_20ms = parse_histogram_file(file_vanilla_20ms)
    values_vanilla_80ms, percentiles_vanilla_80ms, inv_p_vanilla_80ms = parse_histogram_file(file_vanilla_80ms)
    values_xkernel_20ms, percentiles_xkernel_20ms, inv_p_xkernel_20ms = parse_histogram_file(file_xkernel_20ms)
    values_xkernel_80ms, percentiles_xkernel_80ms, inv_p_xkernel_80ms = parse_histogram_file(file_xkernel_80ms)
    
    # Filter: remove infinite values and values beyond p999
    # p999 corresponds to inv_p=1000, but data may have points slightly beyond
    # Allow inv_p up to ~1100 to include the closest point to p999 (inv_p=1024)
    p999_inv_p_max = 110000.0  # Allow slightly beyond 1000 to include closest data point
    
    mask_vanilla_20ms = np.isfinite(inv_p_vanilla_20ms) & (inv_p_vanilla_20ms <= p999_inv_p_max)
    mask_vanilla_80ms = np.isfinite(inv_p_vanilla_80ms) & (inv_p_vanilla_80ms <= p999_inv_p_max)
    mask_xkernel_20ms = np.isfinite(inv_p_xkernel_20ms) & (inv_p_xkernel_20ms <= p999_inv_p_max)
    mask_xkernel_80ms = np.isfinite(inv_p_xkernel_80ms) & (inv_p_xkernel_80ms <= p999_inv_p_max)
    
    x_vanilla_20ms = inv_p_vanilla_20ms[mask_vanilla_20ms]
    y_vanilla_20ms = values_vanilla_20ms[mask_vanilla_20ms] / 1000  # convert to seconds
    x_vanilla_80ms = inv_p_vanilla_80ms[mask_vanilla_80ms]
    y_vanilla_80ms = values_vanilla_80ms[mask_vanilla_80ms] / 1000  # convert to seconds
    x_xkernel_20ms = inv_p_xkernel_20ms[mask_xkernel_20ms]
    y_xkernel_20ms = values_xkernel_20ms[mask_xkernel_20ms] / 1000  # convert to seconds
    x_xkernel_80ms = inv_p_xkernel_80ms[mask_xkernel_80ms]
    y_xkernel_80ms = values_xkernel_80ms[mask_xkernel_80ms] / 1000  # convert to seconds
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Plot all datasets: X-axis is 1/(1-Percentile), Y-axis is latency value
    ax.plot(x_vanilla_20ms, y_vanilla_20ms, 
            color=plot_common.colors[2], linewidth=2, label='SF=3 (20ms RTT)', zorder=2, marker=plot_common.markers[0], markersize=8, markevery=10)
    ax.plot(x_xkernel_20ms, y_xkernel_20ms, 
            color=plot_common.colors[2], linestyle='--', linewidth=2, label='SF=1 (20ms RTT)', zorder=2, marker=plot_common.markers[1], markersize=8, markevery=10)
    ax.plot(x_vanilla_80ms, y_vanilla_80ms, 
            color=plot_common.colors[4], linewidth=2, label='SF=3 (80ms RTT)', zorder=2, marker=plot_common.markers[0], markersize=8, markevery=10)
    ax.plot(x_xkernel_80ms, y_xkernel_80ms, 
            color=plot_common.colors[4], linestyle='--', linewidth=2, label='SF=1 (80ms RTT)', zorder=2, marker=plot_common.markers[1], markersize=8, markevery=10)
    
    # Set x-axis to log scale (HistogramLogProcessor style)
    ax.set_xscale('log')
    # Y-axis is linear scale
    ax.set_yscale('linear')
    
    # Set custom x-axis ticks and labels: only show 0, p90, p99, p999
    # Calculate 1/(1-p) for key percentiles
    key_inv_p = [
        1.0,      # p0: 1/(1-0) = 1
        10.0,     # p90: 1/(1-0.9) = 10
        100.0,    # p99: 1/(1-0.99) = 100
        1000.0,    # p999: 1/(1-0.999) = 1000
        10000.0,   # p9999: 1/(1-0.9999) = 10000
        100000.0  # p99999: 1/(1-0.99999) = 100000
    ]
    key_labels = ['0', 'p90', 'p99', 'p99.9', 'p99.99', 'p99.999']
    
    ax.set_xticks(key_inv_p)
    ax.set_xticklabels(key_labels)
    
    y_ticks = np.arange(0, 13, 4)
    ax.set_yticks(y_ticks)
    ax.set_ylim([0, 12])
    
    # Set x-axis limit: right boundary is p999 (inv_p=1000)
    p999_inv_p = 100000.0  # 1/(1-0.99999) = 100000
    ax.set_xlim([1.0, p999_inv_p])
    
    # Labels and title
    ax.set_xlabel('Percentile')
    ax.set_ylabel('FCT (seconds)')
    
    # Grid and limits
    ax.grid(True, alpha=0.3, which='both', zorder=0)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Make axis lines thicker
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_linewidth(1)
    
    # Legend
    ax.legend(loc='best', frameon=True, facecolor='white', framealpha=1.0)
    
    plt.tight_layout()
    plot_common.save_fig(script_dir, 'nginx_tail_static')
    plt.close()
    
    print(f"Plot saved to {os.path.join(script_dir, 'nginx_tail_static.pdf')}")

if __name__ == '__main__':
    plot_histogram_tail()

