import matplotlib.pyplot as plt
import numpy as np
import os
import re
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from plot_common import colors, save_fig, hatches

# Set font to use system default instead of Arial
plt.rcParams['font.family'] = 'DejaVu Sans'

def parse_metric_result(file_path):
    """Parse metric file to extract unplug request counts"""
    unplug_counts = []
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                # Look for block_unplug lines and extract the number
                match = re.search(r'block_unplug:.*?(\d+)$', line)
                if match:
                    count = int(match.group(1))
                    unplug_counts.append(count)
                    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    # Calculate statistics
    if unplug_counts:
        avg_count = np.mean(unplug_counts)
        max_count = np.max(unplug_counts)
        min_count = np.min(unplug_counts)
        return {
            'avg': avg_count,
            'max': max_count,
            'min': min_count,
            'counts': unplug_counts
        }
    else:
        return {
            'avg': 0,
            'max': 0,
            'min': 0,
            'counts': []
        }

def collect_data():
    """Collect unplug data from pure workload metric files"""
    results_dir = "../results/blk-mq"
    
    # Define the test scenarios for pure workloads
    scenarios = {
        'write': ['write_32_metric.txt', 'write_128_metric.txt'],
        'read': ['read_32_metric.txt', 'read_128_metric.txt']
    }
    
    data = {}
    
    for scenario, files in scenarios.items():
        data[scenario] = {}
        for file in files:
            file_path = os.path.join(results_dir, file)
            if os.path.exists(file_path):
                unplug_stats = parse_metric_result(file_path)
                
                # Determine blk_max_request_count from filename
                if '32' in file:
                    blk_count = 32
                elif '128' in file:
                    blk_count = 128
                else:
                    continue
                    
                data[scenario][blk_count] = unplug_stats
    
    return data

def create_bar_chart(data):
    """Create bar chart showing unplug request counts for pure workloads"""
    scenarios = list(data.keys())
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Define bar positions - separate positions for each scenario
    x = np.arange(len(scenarios))
    width = 0.35  # Width of each bar
    
    # Create bars for each combination
    bars = []
    labels = []
    
    # For write scenario: only show write data
    write_32_data = [data['write'].get(32, {}).get('avg', 0)]
    write_128_data = [data['write'].get(128, {}).get('avg', 0)]
    
    # For read scenario: only show read data
    read_32_data = [data['read'].get(32, {}).get('avg', 0)]
    read_128_data = [data['read'].get(128, {}).get('avg', 0)]
    
    # Write bars (at x=0)
    bar1 = ax.bar(0 - width/2, write_32_data, width, label='32', 
                  color='white', linewidth=2, edgecolor=colors[0], alpha=0.8, hatch=hatches[7])
    bars.append(bar1)
    labels.append('32')
    
    bar2 = ax.bar(0 + width/2, write_128_data, width, label='128', 
                  color='white', linewidth=4, edgecolor=colors[1], alpha=0.8, hatch=hatches[0])
    bars.append(bar2)
    labels.append('128')
    
    # Read bars (at x=1)
    bar3 = ax.bar(1 - width/2, read_32_data, width, label='32', 
                  color='white', linewidth=2, edgecolor=colors[0], alpha=0.8, hatch=hatches[7])
    bars.append(bar3)
    labels.append('32')
    
    bar4 = ax.bar(1 + width/2, read_128_data, width, label='128', 
                  color='white', linewidth=4, edgecolor=colors[1], alpha=0.8, hatch=hatches[0])
    bars.append(bar4)
    labels.append('128')
    
    # Customize the plot
    ax.set_xlabel('Workload Type', fontsize=20)
    ax.set_ylabel('Unplug Request Count', fontsize=20)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 50, 100, 150])
    ax.set_xticklabels(['write', 'read'], fontsize=20)
    ax.legend(fontsize=16, ncol=4, loc='best')
    ax.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        for rect in bar:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{int(height)}',
                           xy=(rect.get_x() + rect.get_width() / 2, height),
                           xytext=(0, 3),  # 3 points vertical offset
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=16)
    
    plt.tight_layout()
    return fig

def main():
    # Collect data
    print("Collecting unplug data from pure workload metric files...")
    data = collect_data()
    
    # Print collected data for verification
    print("\nCollected data:")
    for scenario, blk_data in data.items():
        print(f"\n{scenario}:")
        for blk_count, stats in blk_data.items():
            print(f"  blk_max_request_count={blk_count}: avg={stats['avg']:.1f}, max={stats['max']}, min={stats['min']}")
    
    # Create and save the chart
    print("\nCreating bar chart...")
    fig = create_bar_chart(data)
    
    # Save the figure
    fig_name = "pure_workload_unplug"
    plt.savefig(f"{fig_name}.pdf", bbox_inches='tight', dpi=300)
    
    print(f"Chart saved as {fig_name}.pdf")
    plt.show()

if __name__ == "__main__":
    main()
