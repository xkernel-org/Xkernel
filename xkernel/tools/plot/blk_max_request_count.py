import matplotlib.pyplot as plt
import numpy as np
import os
import re
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from plot_common import colors, save_fig, hatches

# Set font to use system default instead of Arial
plt.rcParams['font.family'] = 'DejaVu Sans'

def parse_fio_result(file_path):
    """Parse fio result file to extract read and write throughput"""
    read_tpt = 0
    write_tpt = 0
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Extract read throughput
        read_match = re.search(r'READ: bw=([\d.]+)([KMGT]iB/s)', content)
        if read_match:
            value = float(read_match.group(1))
            unit = read_match.group(2)
            if unit == 'KiB/s':
                read_tpt = value / 1024  # Convert to MiB/s
            elif unit == 'MiB/s':
                read_tpt = value
            elif unit == 'GiB/s':
                read_tpt = value * 1024
                
        # Extract write throughput
        write_match = re.search(r'WRITE: bw=([\d.]+)([KMGT]iB/s)', content)
        if write_match:
            value = float(write_match.group(1))
            unit = write_match.group(2)
            if unit == 'KiB/s':
                write_tpt = value / 1024  # Convert to MiB/s
            elif unit == 'MiB/s':
                write_tpt = value
            elif unit == 'GiB/s':
                write_tpt = value * 1024
                
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        
    return read_tpt, write_tpt

def collect_data():
    """Collect throughput data from all fio result files"""
    results_dir = "../results/blk-mq"
    
    # Define the test scenarios
    scenarios = {
        # 'write': ['write_32_fio.txt', 'write_128_fio.txt'],
        '25%': ['mix_25_32_fio.txt', 'mix_25_128_fio.txt'],
        '50%': ['mix_50_32_fio.txt', 'mix_50_128_fio.txt'],
        '75%': ['mix_75_32_fio.txt', 'mix_75_128_fio.txt'],
        # 'read': ['read_32_fio.txt', 'read_128_fio.txt']
    }
    
    data = {}
    
    for scenario, files in scenarios.items():
        data[scenario] = {}
        for file in files:
            file_path = os.path.join(results_dir, file)
            if os.path.exists(file_path):
                read_tpt, write_tpt = parse_fio_result(file_path)
                
                # Determine blk_max_request_count from filename
                if '32' in file:
                    blk_count = 32
                elif '128' in file:
                    blk_count = 128
                else:
                    continue
                    
                data[scenario][blk_count] = {
                    'read_tpt': read_tpt,
                    'write_tpt': write_tpt
                }
    
    return data

def create_bar_chart(data):
    """Create bar chart showing throughput for different scenarios"""
    scenarios = list(data.keys())
    blk_counts = [32, 128]
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define bar positions
    x = np.arange(len(scenarios))
    width = 0.2  # Width of each bar
    
    # Create bars for each combination
    bars = []
    labels = []
    
    # 32 read
    read_32_data = [data[scenario].get(32, {}).get('read_tpt', 0) for scenario in scenarios]
    bar1 = ax.bar(x - 1.5*width, read_32_data, width, label='Read (32)', color='white', linewidth=2,edgecolor=colors[0], alpha=0.8, hatch=hatches[7])
    bars.append(bar1)
    labels.append('Read (32)')
    
    # 128 read
    read_128_data = [data[scenario].get(128, {}).get('read_tpt', 0) for scenario in scenarios]
    bar2 = ax.bar(x - 0.5*width, read_128_data, width, label='Read (128)', color='white', linewidth=4,edgecolor=colors[1], alpha=0.8, hatch=hatches[0])
    bars.append(bar2)
    labels.append('Read (128)')
    
    # 32 write
    write_32_data = [data[scenario].get(32, {}).get('write_tpt', 0) for scenario in scenarios]
    bar3 = ax.bar(x + 0.5*width, write_32_data, width, label='Write (32)', color='white', linewidth=2,edgecolor=colors[2], alpha=0.8, hatch=hatches[7])
    bars.append(bar3)
    labels.append('Write (32)')
    
    # 128 write
    write_128_data = [data[scenario].get(128, {}).get('write_tpt', 0) for scenario in scenarios]
    bar4 = ax.bar(x + 1.5*width, write_128_data, width, label='Write (128)', color='white', linewidth=4,edgecolor=colors[3], alpha=0.8, hatch=hatches[0])
    bars.append(bar4)
    labels.append('Write (128)')
    
    # Customize the plot
    ax.set_xlabel('Read/Write Ratio', fontsize=20)
    ax.set_ylabel('Throughput (MiB/s)', fontsize=20)
    ax.set_xticks(x)
    ax.set_ylim(0, 10)
    ax.set_xticklabels(scenarios, fontsize=20)
    ax.legend(fontsize=20)
    ax.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        for rect in bar:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height:.1f}',
                           xy=(rect.get_x() + rect.get_width() / 2, height),
                           xytext=(0, 3),  # 3 points vertical offset
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=20)
    
    plt.tight_layout()
    return fig

def main():
    # Collect data
    print("Collecting data from fio result files...")
    data = collect_data()
    
    # Print collected data for verification
    print("\nCollected data:")
    for scenario, blk_data in data.items():
        print(f"\n{scenario}:")
        for blk_count, tpt_data in blk_data.items():
            print(f"  blk_max_request_count={blk_count}: read={tpt_data['read_tpt']:.1f} MiB/s, write={tpt_data['write_tpt']:.1f} MiB/s")
    
    # Create and save the chart
    print("\nCreating bar chart...")
    fig = create_bar_chart(data)
    
    # Save the figure
    fig_name = "blk_max_request_count_throughput"
    plt.savefig(f"{fig_name}.pdf", bbox_inches='tight', dpi=300)
    
    print(f"Chart saved as {fig_name}.pdf")
    plt.show()

if __name__ == "__main__":
    main()
