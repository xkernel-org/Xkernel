#!/usr/bin/env python3
"""
Script to plot a CDF from numerical data in a text file.
Usage: python plot_cdf.py [input_file]
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def read_data(filename):
    """Read numerical data from file, one number per line."""
    data = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line:  # Skip empty lines
                try:
                    data.append(float(line))
                except ValueError:
                    # Skip lines that aren't valid numbers
                    pass
    return np.array(data)


def compute_cdf(data):
    """Compute CDF values for the data."""
    # Sort the data
    sorted_data = np.sort(data)
    # Compute the CDF values (cumulative probabilities)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    return sorted_data, cdf


def plot_cdf(data, output_file=None):
    """Plot the CDF of the data."""
    sorted_data, cdf = compute_cdf(data)

    plt.figure(figsize=(10, 6))
    plt.plot(sorted_data, cdf, linewidth=2, marker='o', markersize=3)
    plt.grid(True, alpha=0.3)
    plt.xlabel('Value', fontsize=12)
    plt.ylabel('Cumulative Probability', fontsize=12)
    plt.title('Cumulative Distribution Function (CDF)', fontsize=14, fontweight='bold')
    plt.ylim([0, 1.05])

    # Add statistics as text
    stats_text = f'n = {len(data)}\n'
    stats_text += f'Mean = {np.mean(data):.2f}\n'
    stats_text += f'Median = {np.median(data):.2f}\n'
    stats_text += f'Min = {np.min(data):.2f}\n'
    stats_text += f'Max = {np.max(data):.2f}'
    plt.text(0.02, 0.98, stats_text,
             transform=plt.gca().transAxes,
             verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
             fontsize=10)

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"CDF plot saved to: {output_file}")
    else:
        plt.show()


def main():
    # Default to len.txt if no argument provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'len.txt'

    # Check if file exists
    if not Path(input_file).exists():
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    # Read data
    data = read_data(input_file)

    if len(data) == 0:
        print("Error: No valid numerical data found in file.")
        sys.exit(1)

    print(f"Loaded {len(data)} data points from {input_file}")
    print(f"Statistics:")
    print(f"  Mean: {np.mean(data):.2f}")
    print(f"  Median: {np.median(data):.2f}")
    print(f"  Std Dev: {np.std(data):.2f}")
    print(f"  Min: {np.min(data):.0f}")
    print(f"  Max: {np.max(data):.0f}")

    # Generate output filename
    input_path = Path(input_file)
    output_file = input_path.parent / f"{input_path.stem}_cdf.png"

    # Plot CDF
    plot_cdf(data, output_file=output_file)


if __name__ == '__main__':
    main()

