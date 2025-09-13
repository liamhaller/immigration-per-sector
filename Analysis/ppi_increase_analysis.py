"""
PPI Increase Analysis

Analyzes which NAICS categories have had the largest increase in Producer Price Index 
since 2015 and creates a GM-style formatted chart of the top 5 categories.
"""

from pathlib import Path
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import get_logger, AnalysisSession, gm_formatting, processed_data_dir, create_analysis_session

logger = get_logger(__name__)

# Create analysis session for organized output
session = create_analysis_session("ppi_increase_analysis")
# AnalysisSession creates timestamped output directories for organizing analysis results
# Use session.dir to save files directly: df.to_csv(session.dir / 'data.csv'), fig.savefig(session.dir / 'plot.png')
# Use session.save() for text content: session.save('summary.txt', results_text) -- avoid opening/closing files
# All outputs are saved to output/analysis_name/YYYY-MM-DD_HH-MM-SS/


def load_ppi_data():
    """Load the processed three-digit PPI data."""
    logger.info("Loading processed PPI data")
    
    ppi_path = processed_data_dir / "three_digit_ppi.csv"
    if not ppi_path.exists():
        raise FileNotFoundError(f"Processed PPI data not found at {ppi_path}. Run DataProcessing/process_bls_ppi.py first.")
    
    df = pd.read_csv(ppi_path)
    logger.info(f"Loaded {len(df)} PPI records")
    
    # Convert time to datetime for easier filtering
    df['time_dt'] = pd.to_datetime(df['time'])
    
    return df


def calculate_ppi_increases(df):
    """Calculate PPI percentage increases for each NAICS category since 2015."""
    logger.info("Calculating PPI percentage increases since 2015")
    
    # Get baseline values (earliest available in 2015)
    baseline_data = df[df['time_dt'].dt.year == 2015].groupby('NAICS')['value'].first().reset_index()
    baseline_data.columns = ['NAICS', 'baseline_value']
    
    # Get latest values
    latest_data = df.loc[df.groupby('NAICS')['time_dt'].idxmax()].reset_index(drop=True)
    latest_data = latest_data[['NAICS', 'value', 'time']]
    latest_data.columns = ['NAICS', 'latest_value', 'latest_time']
    
    # Merge baseline and latest values
    comparison_data = baseline_data.merge(latest_data, on='NAICS', how='inner')
    
    # Calculate percentage increase
    comparison_data['ppi_increase_pct'] = (
        (comparison_data['latest_value'] - comparison_data['baseline_value']) / 
        comparison_data['baseline_value'] * 100
    )
    
    logger.info(f"Calculated increases for {len(comparison_data)} NAICS categories")
    
    return comparison_data


def get_top5_categories(comparison_data):
    """Identify the top 5 NAICS categories with largest PPI percentage increases."""
    logger.info("Identifying top 5 categories with largest PPI percentage increases")
    
    # Sort by percentage increase
    top5 = comparison_data.nlargest(5, 'ppi_increase_pct').copy()
    
    logger.info("Top 5 categories with largest PPI increases:")
    for _, row in top5.iterrows():
        logger.info(f"  NAICS {row['NAICS']}: +{row['ppi_increase_pct']:.1f}%")
    
    return top5


def create_time_series_chart(df, top5_naics, session):
    """Create a GM-style time series chart for the top 5 categories."""
    logger.info("Creating time series chart for top 5 categories")
    
    # Filter data for top 5 NAICS categories
    chart_data = df[df['NAICS'].isin(top5_naics['NAICS'])].copy()
    
    # Pivot data for charting
    chart_pivot = chart_data.pivot(index='time', columns='NAICS', values='value')
    chart_pivot.index = pd.to_datetime(chart_pivot.index)
    chart_pivot = chart_pivot.sort_index()
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(chart_pivot)
    
    # Apply GM formatting
    gm_formatting(
        ax=ax,
        title="Producer Price Index: Top 5 Categories with Largest Increases Since 2015",
        data=chart_pivot,
        ylabel="PPI Value"
    )
    
    chart_path = session.dir / "top5_ppi_increases_timeseries.png"
    plt.savefig(chart_path, dpi=400, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Time series chart saved to {chart_path}")
    return chart_path


def create_increase_comparison_chart(top5, session):
    """Create a GM-style bar chart comparing the PPI percentage increases."""
    logger.info("Creating PPI increase comparison chart")
    
    # Prepare data for bar chart
    chart_data = pd.DataFrame({
        'PPI Increase (%)': top5['ppi_increase_pct'].values
    }, index=top5['NAICS'])
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(range(len(chart_data)), chart_data['PPI Increase (%)'])
    ax.set_xticks(range(len(chart_data)))
    ax.set_xticklabels(chart_data.index)
    
    # Apply GM formatting
    gm_formatting(
        ax=ax,
        title="Top 5 NAICS Categories: PPI Percentage Increases Since 2015",
        ylabel="PPI Increase (%)",
        xlabel="NAICS Code"
    )
    
    chart_path = session.dir / "top5_ppi_increases_comparison.png"
    plt.savefig(chart_path, dpi=400, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Comparison chart saved to {chart_path}")
    return chart_path


def save_results(comparison_data, top5, session):
    """Save analysis results to CSV files."""
    logger.info("Saving analysis results")
    
    # Save full comparison data
    full_results_path = session.dir / "ppi_increases_all_categories.csv"
    comparison_data_sorted = comparison_data.sort_values('ppi_increase_pct', ascending=False)
    comparison_data_sorted.to_csv(full_results_path, index=False)
    logger.info(f"Full results saved to {full_results_path}")
    
    # Save top 5 results
    top5_results_path = session.dir / "ppi_increases_top5.csv"
    top5.to_csv(top5_results_path, index=False)
    logger.info(f"Top 5 results saved to {top5_results_path}")
    
    return full_results_path, top5_results_path


def main():
    """Analyze PPI increases and create visualizations."""
    logger.info("Starting PPI increase analysis")
    
    try:
        # Load and analyze data
        df = load_ppi_data()
        comparison_data = calculate_ppi_increases(df)
        top5 = get_top5_categories(comparison_data)
        
        # Create visualizations
        timeseries_chart = create_time_series_chart(df, top5, session)
        comparison_chart = create_increase_comparison_chart(top5, session)
        
        # Save results
        full_results, top5_results = save_results(comparison_data, top5, session)
        
        # Log summary
        logger.info("=== ANALYSIS COMPLETE ===")
        logger.info(f"Output directory: {session.dir}")
        logger.info(f"Charts created: {timeseries_chart.name}, {comparison_chart.name}")
        logger.info(f"Data files: {full_results.name}, {top5_results.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"PPI increase analysis failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
else:
    # Also run when imported from .qmd
    main()