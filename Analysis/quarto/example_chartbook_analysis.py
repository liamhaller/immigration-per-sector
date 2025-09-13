"""
PPI 2025 Movement Analysis for Chartbook

This analysis creates DataFrames for PPI movements by NAICS in 2025.
Structured for direct import into Quarto notebooks - produces variables rather than functions.
"""

from pathlib import Path
import sys
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import processed_data_dir

# No logging for quarto modules to keep output clean

# Load the processed three-digit PPI data
ppi_df = pd.read_csv(processed_data_dir / "three_digit_ppi.csv")
ppi_df['time'] = pd.to_datetime(ppi_df['time'])
# Ensure NAICS codes are strings for proper display
ppi_df['NAICS'] = ppi_df['NAICS'].astype(str)

########### Calculate 2025 PPI movements ##############

# Get December 2024 baseline and latest 2025 data
baseline_data = ppi_df[ppi_df['time'] == '2024-12-01'][['NAICS', 'value']].rename(columns={'value': 'baseline_value'})
latest_data = ppi_df[ppi_df['time'].dt.year == 2025].groupby('NAICS')['value'].last().reset_index().rename(columns={'value': 'latest_value'})

# Calculate movements
movement_data = baseline_data.merge(latest_data, on='NAICS')
movement_data['percent_change'] = ((movement_data['latest_value'] - movement_data['baseline_value']) / movement_data['baseline_value']) * 100

########### Create analysis datasets for Quarto ##############

# Top 5 largest increases
top5_increases = (movement_data.nlargest(5, 'percent_change')
                 .round({'baseline_value': 1, 'latest_value': 1, 'percent_change': 2})
                 .reset_index(drop=True))

# Top 5 largest decreases  
top5_decreases = (movement_data.nsmallest(5, 'percent_change')
                 .round({'baseline_value': 1, 'latest_value': 1, 'percent_change': 2})
                 .reset_index(drop=True))


# Time series data for top 5 biggest movers (line chart)
movement_data['abs_change'] = movement_data['percent_change'].abs()
top5_movers = movement_data.nlargest(5, 'abs_change')
top5_movers_naics = top5_movers['NAICS'].tolist()
top5_timeseries = ppi_df[ppi_df['NAICS'].isin(top5_movers_naics)]
top5_chart_data = (top5_timeseries.pivot(index='time', columns='NAICS', values='value')
                   .ffill())

# Sort columns by movement size for consistent ordering
movement_order = top5_movers.sort_values('abs_change', ascending=False)['NAICS'].tolist()
top5_chart_data = top5_chart_data[movement_order]

# Analysis summary
latest_date = ppi_df[ppi_df['time'].dt.year == 2025]['time'].max()
analysis_period = f"Dec 2024 to {latest_date.strftime('%b %Y')}"

# Analysis complete - variables available for Quarto