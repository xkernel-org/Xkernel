import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Load the CSV file
df = pd.read_csv('sysctl_analysis_v1.csv')

# Filter 1: End Year is not empty AND Domain is empty (const to sysctl)
filtered_df1 = df[(df['End Year'].notna()) & (df['Domain'].isna())]
sysctl_col = filtered_df1.columns[0]
plot_data1 = filtered_df1.sort_values(by=sysctl_col, key=lambda x: x.str.lower()).reset_index(drop=True)

# Filter 2: End Year is not empty AND Domain equals 1 (const domain change)
filtered_df2 = df[(df['End Year'].notna()) & (df['Domain'] == 1)]
plot_data2 = filtered_df2.sort_values(by=sysctl_col, key=lambda x: x.str.lower()).reset_index(drop=True)

print(f"Const to Sysctl: {len(plot_data1)} items")
print(f"Const Domain Change: {len(plot_data2)} items")

# Create single figure with combined data
total_items = len(plot_data1) + len(plot_data2)
fig, ax = plt.subplots(figsize=(total_items * 0.3, 10))

# Left side: Const to Sysctl (Domain is empty)
x_positions_1 = np.arange(len(plot_data1))
start_years_1 = plot_data1['Start Year'].values
end_years_1 = plot_data1['End Year'].values

# Right side: Const Domain Change (Domain = 1)
x_positions_2 = np.arange(len(plot_data1), len(plot_data1) + len(plot_data2))
start_years_2 = plot_data2['Start Year'].values
end_years_2 = plot_data2['End Year'].values

# Set x-axis positions for each sysctl with numbered labels
all_x_positions = np.concatenate([x_positions_1, x_positions_2])
ax.set_xticks(all_x_positions)
ax.set_xticklabels(range(1, len(all_x_positions) + 1), rotation=90)

# Set x-axis limits to remove extra white space
ax.set_xlim(-0.5, len(all_x_positions) - 0.5)

# Set y-axis with year range - boxes are now 1.0 x 1.0 squares
min_year = 2005
max_year = int(max(np.max(end_years_1), np.max(end_years_2))) + 1
# Y-axis limits based on box positions (1.0 per year)
# Upper limit needs to be y_max + 1.0 to include the full height of the last box
y_max = min_year + (max_year - min_year) * 1.0
# Category labels will be placed just above y_max + 1.0 (outside the plot area)
category_row_y = y_max + 1.4
ax.set_ylim(min_year, y_max + 1.0)

# Set y-axis ticks to show every 5 years at the center of each box
y_tick_years = np.arange(min_year, max_year + 1, 5)
y_tick_positions = [min_year + (year - min_year) * 1.0 + 0.5 for year in y_tick_years]
ax.set_yticks(y_tick_positions)
# Format year labels to show only last two digits (e.g., 05, 10, 15, 25)
ax.set_yticklabels([f"{str(int(year))[-2:]}" for year in y_tick_years])

# Remove tick marks (keep labels only)
ax.tick_params(axis='both', which='both', length=0)

# Add "Year" label at the top of the y-axis
ax.text(0, y_max + 2, 'Year', fontweight='bold', 
        ha='right', va='top', rotation=0)

# Set aspect ratio so circles are touching when years are adjacent
ax.set_aspect('equal', adjustable='box')

# Add grid lines for both axes (draw first so circles appear on top)
# ax.grid(True, axis='both', alpha=0.3, linestyle='--')

# Apply tight_layout first before calculating marker size
plt.tight_layout()

# Calculate marker size so circles touch - diameter = 1 year in data coordinates
# We need to convert from data coordinates to points
fig_height_inches = fig.get_figheight()
ax_height = ax.get_position().height
y_range = max_year - min_year + 1
points_per_inch = 72
# Size in points for 1 data unit
marker_size_points = (fig_height_inches * ax_height * points_per_inch) / y_range
# Scatter uses area, so we need to square the radius (diameter/2)
marker_size = (marker_size_points) ** 2

# Color configuration for boxes
CONST_COLOR = '0.95'  # White for constant state
SYSCTL_COLOR = plot_common.colors[2]  # Blue for sysctl state
DOMAIN_CHANGE_COLOR = plot_common.colors[4]  # Orange for after domain change

# Box dimensions: 1.0 x 1.0 (strict square boxes) with zero spacing - adjacent boxes touch both horizontally and vertically
from matplotlib.patches import Rectangle
box_height = 1.0
box_width = 1.0

# Create mapping from year to y-position (boxes stacked with no vertical gap)
def year_to_y_pos(year):
    year_index = year - min_year
    return min_year + year_index * 1.0  # Each box is 1.0 tall

# Plot boxes for Const to Sysctl (Domain is empty, LEFT side now)
# Before start: no box
# After start to end: filled with CONST_COLOR (white)
# After end: filled with SYSCTL_COLOR
for i, (x_pos, start, end) in enumerate(zip(x_positions_1, start_years_1, end_years_1)):
    for year in range(min_year, max_year + 1):
        if year < int(start):
            # Before start year: no box
            continue
        y_pos = year_to_y_pos(year)
        if year >= int(start) and year < int(end):
            # From start to before end: filled with CONST_COLOR (white)
            rect = Rectangle((x_pos - box_width/2, y_pos), box_width, box_height,
                           facecolor=CONST_COLOR, edgecolor='black', linewidth=0.75, linestyle='--', zorder=3)
            ax.add_patch(rect)
        else:
            # End year and after: filled with SYSCTL_COLOR
            rect = Rectangle((x_pos - box_width/2, y_pos), box_width, box_height,
                           facecolor=SYSCTL_COLOR, edgecolor='black', linewidth=0.75, linestyle='--', zorder=3)
            ax.add_patch(rect)

# Plot boxes for Const Domain Change (Domain = 1, RIGHT side now)
# Before start: no box
# After start to end: filled with SYSCTL_COLOR
# After end: filled with DOMAIN_CHANGE_COLOR
for i, (x_pos, start, end) in enumerate(zip(x_positions_2, start_years_2, end_years_2)):
    for year in range(min_year, max_year + 1):
        if year < int(start):
            # Before start year: no box
            continue
        y_pos = year_to_y_pos(year)
        if year >= int(start) and year < int(end):
            # From start to before end: filled with SYSCTL_COLOR
            rect = Rectangle((x_pos - box_width/2, y_pos), box_width, box_height,
                           facecolor=SYSCTL_COLOR, edgecolor='black', linewidth=0.75, linestyle='--', zorder=3)
            ax.add_patch(rect)
        else:
            # End year and after: filled with DOMAIN_CHANGE_COLOR
            rect = Rectangle((x_pos - box_width/2, y_pos), box_width, box_height,
                           facecolor=DOMAIN_CHANGE_COLOR, edgecolor='black', linewidth=0.75, linestyle='--', zorder=3)
            ax.add_patch(rect)

# Add category labels in the last constant box (left side only)
category_col = 'Motivation(0/1/2), 0:Hardware/Scale Mismatch; 1:Workload-Specific Tuning; 2:Heuristics & Control'
category_map = {0: 'H', 1: 'A', 2: 'C'}

# Draw category labels for left side (plot_data1) - in the last constant box before sysctl
for i, x_pos in enumerate(x_positions_1):
    if i < len(plot_data1):
        category_value = plot_data1.iloc[i][category_col]
        end_year = int(plot_data1.iloc[i]['End Year'])
        if pd.notna(category_value):
            label = category_map.get(int(category_value), '')
            # Place label in the center of the last constant box (year before end_year)
            label_y = year_to_y_pos(end_year - 1) + 0.4
            ax.text(x_pos, label_y, label, 
                    ha='center', va='center', fontweight='bold', zorder=5)

# Add diagonal line markers for bugs in Domain is empty items (left side)
for i, (x_pos, row) in enumerate(zip(x_positions_1, plot_data1.itertuples())):
    if pd.notna(row.bugAdd) and pd.notna(row.bugFix):
        bug_start = int(row.bugAdd)
        bug_end = int(row.bugFix)
        for year in range(bug_start, bug_end + 1):
            y_pos = year_to_y_pos(year)
            # Draw diagonal line at 45 degrees (/)
            ax.plot([x_pos - box_width/2, x_pos + box_width/2], 
                   [y_pos, y_pos + box_height], 
                   color='black', linewidth=marker_size_points/10, solid_capstyle='butt', zorder=4)

# Add diagonal line markers for bugs in Domain = 1 items (right side)
for i, (x_pos, row) in enumerate(zip(x_positions_2, plot_data2.itertuples())):
    if pd.notna(row.bugAdd) and pd.notna(row.bugFix):
        bug_start = int(row.bugAdd)
        bug_end = int(row.bugFix)
        for year in range(bug_start, bug_end + 1):
            y_pos = year_to_y_pos(year)
            # Draw diagonal line at 45 degrees (/)
            ax.plot([x_pos - box_width/2, x_pos + box_width/2], 
                   [y_pos, y_pos + box_height], 
                   color='black', linewidth=marker_size_points/10, solid_capstyle='butt', zorder=4)

# Add solid backslash markers for PotentialBug=1 without actual bug (left side)
for i, (x_pos, row) in enumerate(zip(x_positions_1, plot_data1.itertuples())):
    if row.PotentialBUG == 1 and (pd.isna(row.bugAdd) or pd.isna(row.bugFix)):
        # Draw from end year (when it becomes sysctl) to max_year with backslash (\)
        # Use the End Year from the dataframe directly
        end_year = int(plot_data1.iloc[i]['End Year'])
        for year in range(end_year, max_year + 1):
            y_pos = year_to_y_pos(year)
            # Draw diagonal line at 45 degrees (\) - reversed direction, solid
            ax.plot([x_pos - box_width/2, x_pos + box_width/2], 
                   [y_pos + box_height, y_pos], 
                   color='black', linewidth=marker_size_points/10, 
                   solid_capstyle='butt', zorder=4)

# Add solid backslash markers for PotentialBug=1 without actual bug (right side)
for i, (x_pos, row) in enumerate(zip(x_positions_2, plot_data2.itertuples())):
    if row.PotentialBUG == 1 and (pd.isna(row.bugAdd) or pd.isna(row.bugFix)):
        # Draw from end year (when it becomes sysctl/domain) to max_year with backslash (\)
        # Use the End Year from the dataframe directly
        end_year = int(plot_data2.iloc[i]['End Year'])
        for year in range(end_year, max_year + 1):
            y_pos = year_to_y_pos(year)
            # Draw diagonal line at 45 degrees (\) - reversed direction, solid
            ax.plot([x_pos - box_width/2, x_pos + box_width/2], 
                   [y_pos + box_height, y_pos], 
                   color='black', linewidth=marker_size_points/10, 
                   solid_capstyle='butt', zorder=4)

# Add legend on top
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.legend_handler import HandlerLine2D
import matplotlib.transforms as transforms

# Custom handler to draw diagonal lines in legend (within square space)
class HandlerDiagonalLine(HandlerLine2D):
    def __init__(self, angle=45, **kwargs):
        self.angle = angle
        super().__init__(**kwargs)
    
    def create_artists(self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans):
        # Make diagonal within square space like the boxes
        size = min(width, height)
        x_offset = (width - size) / 2
        y_offset = (height - size) / 2
        
        # Calculate diagonal endpoints based on angle within square
        if self.angle == 45:  # / direction (bottom-left to top-right)
            x = [xdescent + x_offset, xdescent + x_offset + size]
            y = [ydescent + y_offset, ydescent + y_offset + size]
        else:  # -45 degrees, \ direction (top-left to bottom-right)
            x = [xdescent + x_offset, xdescent + x_offset + size]
            y = [ydescent + y_offset + size, ydescent + y_offset]
        
        line = Line2D(x, y, 
                     color=orig_handle.get_color(),
                     linewidth=orig_handle.get_linewidth(),
                     linestyle=orig_handle.get_linestyle(),
                     solid_capstyle=orig_handle.get_solid_capstyle())
        return [line]

# Custom handler to draw square patches in legend
from matplotlib.legend_handler import HandlerPatch
class HandlerSquare(HandlerPatch):
    def create_artists(self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans):
        # Make the patch square by using the smaller of width/height
        size = min(width, height)
        # Center the square
        x_offset = (width - size) / 2
        y_offset = (height - size) / 2
        
        square = Rectangle((xdescent + x_offset, ydescent + y_offset), size, size,
                          facecolor=orig_handle.get_facecolor(),
                          edgecolor=orig_handle.get_edgecolor(),
                          linewidth=orig_handle.get_linewidth(),
                          linestyle=orig_handle.get_linestyle(),
                          transform=trans)
        return [square]

legend_elements = [
    Patch(facecolor=CONST_COLOR, edgecolor='black', linewidth=0.75, linestyle='--', label='constant'),
    Patch(facecolor=SYSCTL_COLOR, edgecolor='black', linewidth=0.75, linestyle='--', label='sysctl'),
    Patch(facecolor=DOMAIN_CHANGE_COLOR, edgecolor='black', linewidth=0.75, linestyle='--', label='per domain'),
    Line2D([0], [0], color='black', linewidth=4, label='buggy', solid_capstyle='butt'),
    Line2D([0], [0], color='black', linewidth=4, 
           label='potential bug', solid_capstyle='butt')
]

handler_map = {
    legend_elements[0]: HandlerSquare(),                    # constant
    legend_elements[1]: HandlerSquare(),                    # sysctl
    legend_elements[2]: HandlerSquare(),                    # per domain
    legend_elements[3]: HandlerDiagonalLine(angle=45),      # buggy: /
    legend_elements[4]: HandlerDiagonalLine(angle=-45)      # potential bug: \
}

ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.12), 
          ncol=5, frameon=True, facecolor='white', framealpha=1.0, handletextpad=0.3, columnspacing=1.0,
          handler_map=handler_map)

# Save the plot
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'years_combined_simple')

# Display the plot
# plt.show()
