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
    """Plot HistogramLogProcessor style tail latency chart and print P999/P9999"""
    # Parse data files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_vanilla_20ms = os.path.join(script_dir, 'vanilla_20ms.txt')
    file_vanilla_80ms = os.path.join(script_dir, 'vanilla_80ms.txt')
    file_xkernel_20ms = os.path.join(script_dir, 'xkernel_20ms.txt')
    file_xkernel_80ms = os.path.join(script_dir, 'xkernel_80ms.txt')
    
    # Parse static files
    file_static_vanilla_20ms = os.path.join(script_dir, 'w3_20ms_sf3.txt')
    file_static_vanilla_80ms = os.path.join(script_dir, 'w3_80ms_sf3.txt')
    file_static_xkernel_20ms = os.path.join(script_dir, 'w3_20ms_sf1.txt')
    file_static_xkernel_80ms = os.path.join(script_dir, 'w3_80ms_sf1.txt')
    
    # Parse all files — keep full arrays for percentile lookup
    values_vanilla_20ms, percentiles_vanilla_20ms, inv_p_vanilla_20ms = parse_histogram_file(file_vanilla_20ms)
    values_vanilla_80ms, percentiles_vanilla_80ms, inv_p_vanilla_80ms = parse_histogram_file(file_vanilla_80ms)
    values_xkernel_20ms, percentiles_xkernel_20ms, inv_p_xkernel_20ms = parse_histogram_file(file_xkernel_20ms)
    values_xkernel_80ms, percentiles_xkernel_80ms, inv_p_xkernel_80ms = parse_histogram_file(file_xkernel_80ms)
    
    # Parse static files
    static_values_vanilla_20ms, static_percentiles_vanilla_20ms, static_inv_p_vanilla_20ms = parse_histogram_file(file_static_vanilla_20ms)
    static_values_vanilla_80ms, static_percentiles_vanilla_80ms, static_inv_p_vanilla_80ms = parse_histogram_file(file_static_vanilla_80ms)
    static_values_xkernel_20ms, static_percentiles_xkernel_20ms, static_inv_p_xkernel_20ms = parse_histogram_file(file_static_xkernel_20ms)
    static_values_xkernel_80ms, static_percentiles_xkernel_80ms, static_inv_p_xkernel_80ms = parse_histogram_file(file_static_xkernel_80ms)

    # --- Print P999 and P9999 latencies ---
    targets = {
        'P999': 0.999,
        'P9999': 0.9999
    }

    datasets = {
        'Vanilla (20ms RTT)': (values_vanilla_20ms, percentiles_vanilla_20ms),
        'Vanilla (80ms RTT)': (values_vanilla_80ms, percentiles_vanilla_80ms),
        'Adaptive SF (20ms RTT)': (values_xkernel_20ms, percentiles_xkernel_20ms),
        'Adaptive SF (80ms RTT)': (values_xkernel_80ms, percentiles_xkernel_80ms),
    }

    print("\n=== Tail Latency (FCT in seconds) ===")
    for name, (vals, pers) in datasets.items():
        print(f"\n{name}:")
        for label, p in targets.items():
            latency_sec = get_latency_at_percentile(vals, pers, p)
            print(f"  {label}: {latency_sec:.6f} s")

    # --- Plotting: apply masks for visualization only ---
    p9999_inv_p_max = 11000.0  # Allow up to slightly beyond 10,000 for p9999 (p99.99, two 9s)
    p99999_inv_p_max = 110000.0  # Allow up to slightly beyond 100,000 for p99999 (p99.999, three 9s)

    def apply_mask(values, percentiles, inv_p, max_inv_p):
        mask = np.isfinite(inv_p) & (inv_p <= max_inv_p)
        return inv_p[mask], values[mask] / 1_000.0  # convert to milliseconds

    # Static data (top subplot) - up to p99.999 (three 9s)
    static_x_vanilla_20ms, static_y_vanilla_20ms = apply_mask(static_values_vanilla_20ms, static_percentiles_vanilla_20ms, static_inv_p_vanilla_20ms, p99999_inv_p_max)
    static_x_vanilla_80ms, static_y_vanilla_80ms = apply_mask(static_values_vanilla_80ms, static_percentiles_vanilla_80ms, static_inv_p_vanilla_80ms, p99999_inv_p_max)
    static_x_xkernel_20ms, static_y_xkernel_20ms = apply_mask(static_values_xkernel_20ms, static_percentiles_xkernel_20ms, static_inv_p_xkernel_20ms, p99999_inv_p_max)
    static_x_xkernel_80ms, static_y_xkernel_80ms = apply_mask(static_values_xkernel_80ms, static_percentiles_xkernel_80ms, static_inv_p_xkernel_80ms, p99999_inv_p_max)
    
    # Adaptive data (bottom subplot) - up to p99.99 (two 9s)
    x_vanilla_20ms, y_vanilla_20ms = apply_mask(values_vanilla_20ms, percentiles_vanilla_20ms, inv_p_vanilla_20ms, p9999_inv_p_max)
    x_vanilla_80ms, y_vanilla_80ms = apply_mask(values_vanilla_80ms, percentiles_vanilla_80ms, inv_p_vanilla_80ms, p9999_inv_p_max)
    x_xkernel_20ms, y_xkernel_20ms = apply_mask(values_xkernel_20ms, percentiles_xkernel_20ms, inv_p_xkernel_20ms, p9999_inv_p_max)
    x_xkernel_80ms, y_xkernel_80ms = apply_mask(values_xkernel_80ms, percentiles_xkernel_80ms, inv_p_xkernel_80ms, p9999_inv_p_max)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
    
    # Top subplot: Static - up to p99.999 (three 9s)
    ax1.set_xscale('log')
    ax1.set_yscale('linear')
    ax1.set_xlim([1.0, 110000.0])
    
    # Calculate y-axis range for static (in milliseconds)
    all_static_y = np.concatenate([static_y_vanilla_20ms, static_y_xkernel_20ms, static_y_vanilla_80ms, static_y_xkernel_80ms])
    static_y_max = np.max(all_static_y) if len(all_static_y) > 0 else 12
    static_y_max = max(static_y_max * 1.1, 12)
    ax1.set_ylim([0, static_y_max])
    
    static_key_inv_p = [1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0]
    static_key_labels = ['0', 'p90', 'p99', 'p99.9', 'p99.99', 'p99.999']
    ax1.set_xticks(static_key_inv_p)
    ax1.set_xticklabels(static_key_labels)  # Show x-axis labels for top subplot
    
    static_y_ticks = np.arange(0, 13, 4)
    ax1.set_yticks(static_y_ticks)
    ax1.set_ylim([0, 12])
    
    # Plot static data
    if len(static_x_vanilla_20ms) > 0 and len(static_y_vanilla_20ms) > 0:
        ax1.plot(static_x_vanilla_20ms, static_y_vanilla_20ms, 
                color=plot_common.colors[2], linewidth=2, label='SF=3 (20ms RTT)', zorder=2, marker=plot_common.markers[0], markersize=8, markevery=10)
    if len(static_x_xkernel_20ms) > 0 and len(static_y_xkernel_20ms) > 0:
        ax1.plot(static_x_xkernel_20ms, static_y_xkernel_20ms, 
                color=plot_common.colors[2], linestyle='--', linewidth=2, label='SF=1 (20ms RTT)', zorder=2, marker=plot_common.markers[1], markersize=8, markevery=10)
    if len(static_x_vanilla_80ms) > 0 and len(static_y_vanilla_80ms) > 0:
        ax1.plot(static_x_vanilla_80ms, static_y_vanilla_80ms, 
                color=plot_common.colors[4], linewidth=2, label='SF=3 (80ms RTT)', zorder=2, marker=plot_common.markers[0], markersize=8, markevery=10)
    if len(static_x_xkernel_80ms) > 0 and len(static_y_xkernel_80ms) > 0:
        ax1.plot(static_x_xkernel_80ms, static_y_xkernel_80ms, 
                color=plot_common.colors[4], linestyle='--', linewidth=2, label='SF=1 (80ms RTT)', zorder=2, marker=plot_common.markers[1], markersize=8, markevery=10)
    
    # No xlabel for top subplot
    ax1.set_xlabel('')
    ax1.set_ylabel('FCT (ms)')
    ax1.grid(True, alpha=0.3, axis='y', linestyle='--', zorder=0)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_linewidth(1)
    ax1.spines['bottom'].set_linewidth(1)
    ax1.legend(loc='best', frameon=True, facecolor='white', framealpha=1.0, fontsize=16)
    
    # Bottom subplot: Adaptive
    ax2.set_xscale('log')
    ax2.set_yscale('linear')
    ax2.set_xlim([1.0, 11000.0])
    
    # Calculate appropriate y-axis range based on actual data (in milliseconds)
    all_y_values = np.concatenate([y_vanilla_20ms, y_xkernel_20ms, y_vanilla_80ms, y_xkernel_80ms])
    y_max = np.max(all_y_values) if len(all_y_values) > 0 else 80
    y_max = max(y_max * 1.1, 80)  # Add 10% padding, minimum 80ms
    ax2.set_ylim([0, y_max])
    
    key_inv_p = [1.0, 10.0, 100.0, 1000.0, 10000.0]
    key_labels = ['0', 'p90', 'p99', 'p99.9', 'p99.99']
    ax2.set_xticks(key_inv_p)
    ax2.set_xticklabels(key_labels)
    
    # Set y-ticks: every 20ms
    y_ticks = np.arange(0, y_max + 20, 20)
    ax2.set_yticks(y_ticks)
    
    # Plot data - ensure we have data points
    if len(x_vanilla_20ms) > 0 and len(y_vanilla_20ms) > 0:
        ax2.plot(x_vanilla_20ms, y_vanilla_20ms, 
                color=plot_common.colors[2], linewidth=2, label='SF=3 (20ms RTT)', zorder=2, marker=plot_common.markers[0], markersize=8, markevery=10)
    if len(x_xkernel_20ms) > 0 and len(y_xkernel_20ms) > 0:
        ax2.plot(x_xkernel_20ms, y_xkernel_20ms, 
                color=plot_common.colors[2], linestyle='--', linewidth=2, label='Adaptive SF (20ms RTT)', zorder=2, marker=plot_common.markers[1], markersize=8, markevery=10)
    if len(x_vanilla_80ms) > 0 and len(y_vanilla_80ms) > 0:
        ax2.plot(x_vanilla_80ms, y_vanilla_80ms, 
                color=plot_common.colors[4], linewidth=2, label='SF=3 (80ms RTT)', zorder=2, marker=plot_common.markers[0], markersize=8, markevery=10)
    if len(x_xkernel_80ms) > 0 and len(y_xkernel_80ms) > 0:
        ax2.plot(x_xkernel_80ms, y_xkernel_80ms, 
                color=plot_common.colors[4], linestyle='--', linewidth=2, label='Adaptive SF (80ms RTT)', zorder=2, marker=plot_common.markers[1], markersize=8, markevery=10)
    
    ax2.set_xlabel('Percentile')
    ax2.set_ylabel('FCT (ms)')
    ax2.grid(True, alpha=0.3, axis='y', linestyle='--', zorder=0)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_linewidth(1)
    ax2.spines['bottom'].set_linewidth(1)
    ax2.legend(loc='best', frameon=True, facecolor='white', framealpha=1.0, fontsize=16)
    
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.25)
    plot_common.save_fig(script_dir, 'nginx_tail')
    plt.close()
    
    print(f"\nPlot saved to {script_dir}/nginx_tail.pdf")


if __name__ == '__main__':
    plot_histogram_tail()