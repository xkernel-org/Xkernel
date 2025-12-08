import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Import plot_common for consistent styling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plot_common

# Load the CSV file
df = pd.read_csv('sysctl_analysis.csv')

# Display basic information
print("DataFrame shape:", df.shape)
print("\nColumn names:")
print(df.columns.tolist())
print("\nFirst few rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)

# Filter: End Year is not empty AND Domain equals 1
filtered_df = df[(df['End Year'].notna()) & (df['Domain'] == 1)]

print(f"\n{'='*60}")
print(f"Filtered data shape: {filtered_df.shape}")
print(f"{'='*60}\n")
print(f"Filtered data:")
print(filtered_df)

# Get the first column (sysctl name)
sysctl_col = filtered_df.columns[0]

# Sort by sysctl name alphabetically
plot_data = filtered_df.sort_values(by=sysctl_col, key=lambda x: x.str.lower()).reset_index(drop=True)

# Create the figure and axis (reduced width from 16 to 12)
fig, ax = plt.subplots(figsize=(12, 10))

# Create horizontal bar plot showing the range from Start Year to End Year
# The bar starts at Start Year and extends to End Year
y_positions = np.arange(len(plot_data))
start_years = plot_data['Start Year'].values
end_years = plot_data['End Year'].values
year_ranges = end_years - start_years  # width of each bar

# Set y-axis labels with sysctl names
ax.set_yticks(y_positions)
ax.set_yticklabels(plot_data[sysctl_col])

# Set labels and title
ax.set_xlabel('Year', fontweight='bold')
ax.set_title('Sysctl Analysis (Year Const Changed Domain)', fontweight='bold')

# Set x-axis with tighter limits to reduce space
min_year = 2005
max_year = int(max(end_years)) + 1
ax.set_xlim(min_year - 0.5, max_year + 0.5)

# Set x-axis ticks to show only integer years (every 2 years for readability)
x_ticks = np.arange(min_year, max_year + 1, 2)
ax.set_xticks(x_ticks)
ax.set_xticklabels([str(int(year)) for year in x_ticks])

# Add horizontal grid lines for y-ticks (draw first so bars appear on top)
ax.grid(True, axis='y', alpha=0.3, linestyle='--')

# Create horizontal bars starting from Start Year with width = (End Year - Start Year)
# Make bars with height=0.6 (increased from 0.4)
# Set zorder high so bars appear on top of grid
bars = ax.barh(y_positions, year_ranges, left=start_years, 
               color=plot_common.colors[4], edgecolor='1', alpha=0.7, height=0.6, zorder=3)

# Add labels on bars showing number of years (end - start)
for i, (bar, start, end) in enumerate(zip(bars, start_years, end_years)):
    # Calculate number of years
    num_years = int(end - start)
    # Position label to the right of the bar
    ax.text(end + 0.3, y_positions[i],
            f'{num_years}',
            ha='left', va='center', fontweight='heavy', color='black')

# Improve layout to prevent label cutoff
plt.tight_layout()

# Save the plot
script_dir = os.path.dirname(os.path.abspath(__file__))
plot_common.save_fig(script_dir, 'years_const_change_domain')

# Display the plot
# plt.show()

print(f"\n{'='*60}")
print("Summary Statistics of Filtered Data:")
print(f"{'='*60}")
print(f"Total number of records: {len(plot_data)}")

# Calculate years count for summary
plot_data['Years_Count'] = plot_data['End Year'] - plot_data['Start Year'] + 1

print(f"\nYears Statistics:")
print(plot_data['Years_Count'].describe())
print(f"\nDetailed breakdown:")
for idx, row in plot_data.iterrows():
    print(f"  {row[sysctl_col]}: {int(row['Years_Count'])} years (from {int(row['Start Year'])} to {int(row['End Year'])})")
