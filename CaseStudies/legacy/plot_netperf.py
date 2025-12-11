import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Data from the screenshots
# Left side: original values
original_data = [59.19, 41.26, 30.70, 19.96, 36.70, 18.63, 46.14, 23.52, 40.02, 17.45]

# Right side: max=32, sf=1
modified_data = [308.86, 310.17, 312.37, 311.16, 310.35, 309.89, 309.43, 310.64, 314.17, 312.79]

# Time in seconds (assuming 10 data points)
time = np.arange(1, len(original_data) + 1)

# Print the ratio of modified/original for each data point
print("Ratio (modified/original) for each time point:")
for i in range(len(original_data)):
    ratio = modified_data[i] / original_data[i]
    print(f"Time {i+1}: {ratio:.2f}x")

# Create figure
fig, ax = plt.subplots(figsize=(8, 3.9))

# Plot the two lines
ax.plot(time, original_data, color=plot_common.colors[2], linewidth=2, marker=plot_common.markers[0], markersize=10, label='original')
ax.plot(time, modified_data, color=plot_common.colors[0], linewidth=2, marker=plot_common.markers[2], markersize=10, label='max=32, sf=1')

# Set labels and limits
ax.set_xlabel('Time (s)')
ax.set_ylabel('Tpt. (Mbps)')
ax.set_xlim(0.5, len(time) + 0.5)
ax.set_ylim(0, max(modified_data) * 1.05)

# Add legend
ax.legend(frameon=True, facecolor='white', framealpha=1.0)

# Add grid
ax.grid(True, alpha=0.3, axis='y')

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Make axis lines thicker
ax.spines['left'].set_linewidth(1)
ax.spines['bottom'].set_linewidth(1)

# Adjust layout and save
plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'netperf')
plt.close()
