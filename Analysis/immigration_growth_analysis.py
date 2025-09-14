"""
Immigration Growth Analysis

Creates charts analyzing employment and earnings growth by immigration share quartiles.
Uses GM-style formatting to visualize relationships between non-citizen workforce share
and economic growth trends across industries.
"""

from pathlib import Path
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import get_logger, gm_formatting, processed_data_dir, create_analysis_session

logger = get_logger(__name__)

# Create analysis session for organized output
session = create_analysis_session("immigration_growth_analysis")


def load_analysis_data():
    """Load the employment and earnings analysis datasets."""
    logger.info("Loading employment and earnings analysis data")

    # Load employment data
    emp_path = processed_data_dir / "employment_immigration_analysis.csv"
    if not emp_path.exists():
        raise FileNotFoundError(f"Employment data not found at {emp_path}")

    employment_df = pd.read_csv(emp_path)
    logger.info(f"Loaded {len(employment_df)} employment records")

    # Load earnings data
    earn_path = processed_data_dir / "earnings_immigration_analysis.csv"
    if not earn_path.exists():
        raise FileNotFoundError(f"Earnings data not found at {earn_path}")

    earnings_df = pd.read_csv(earn_path)
    logger.info(f"Loaded {len(earnings_df)} earnings records")

    return employment_df, earnings_df


# Configuration: Modular immigration grouping
TOP_IMMIGRATION_PERCENTILE = 0.9  # Top 10% of industries by immigration share
HIGH_IMMIGRATION_LABEL = "Top 10% Immigration"
OTHER_INDUSTRIES_LABEL = "All Other Industries"


def create_immigration_groups(df, immigration_col='noncitizen_percentage', top_percentile=TOP_IMMIGRATION_PERCENTILE):
    """Create immigration groups based on top percentile and add to dataframe.

    Args:
        df: DataFrame with immigration data
        immigration_col: Column name for immigration percentage
        top_percentile: Percentile threshold for "high immigration" group (0.9 = top 10%)
    """
    logger.info(f"Creating immigration groups with top {(1-top_percentile)*100:.0f}% of industries")

    # Get unique industries with their immigration percentages
    industry_immigration = df.groupby('industry_code')[immigration_col].first().reset_index()

    # Calculate the percentile threshold
    threshold = industry_immigration[immigration_col].quantile(top_percentile)
    logger.info(f"Top {(1-top_percentile)*100:.0f}% immigration threshold: {threshold:.2f}%")

    # Create groups based on percentile threshold
    industry_immigration['immigration_group'] = industry_immigration[immigration_col].apply(
        lambda x: HIGH_IMMIGRATION_LABEL if x >= threshold else OTHER_INDUSTRIES_LABEL
    )

    # Log group statistics
    group_stats = industry_immigration.groupby('immigration_group')[immigration_col].agg(['count', 'min', 'max', 'mean']).round(2)
    logger.info("Immigration group statistics:")
    for group_name in group_stats.index:
        stats = group_stats.loc[group_name]
        logger.info(f"  {group_name}: {stats['count']} industries, {stats['min']:.2f}%-{stats['max']:.2f}% (avg: {stats['mean']:.2f}%)")

    # Merge groups back to main dataframe
    df_with_groups = df.merge(
        industry_immigration[['industry_code', 'immigration_group']],
        on='industry_code'
    )

    return df_with_groups


def calculate_group_averages(df, growth_col, lookback_months=12):
    """Calculate average growth rates by immigration group and time period.

    Args:
        df: DataFrame with growth data
        growth_col: Column name for growth rates
        lookback_months: Number of months to look back from most recent data
    """
    # Find the most recent date in the data
    df['year_month_dt'] = pd.to_datetime(df['year_month'])
    most_recent_date = df['year_month_dt'].max()
    start_date = most_recent_date - pd.DateOffset(months=lookback_months)

    logger.info(f"Calculating group averages for {growth_col}")
    logger.info(f"Most recent data: {most_recent_date.strftime('%Y-%m-%d')}")
    logger.info(f"Looking back {lookback_months} months to: {start_date.strftime('%Y-%m-%d')}")

    # Filter data from start_date onwards
    df_filtered = df[df['year_month_dt'] >= start_date].copy()
    logger.info(f"Filtered to {len(df_filtered)} records from {start_date.strftime('%Y-%m-%d')} onwards")

    # Group by immigration group and year_month
    group_avg = df_filtered.groupby(['immigration_group', 'year_month'])[growth_col].mean().reset_index()

    # Pivot for charting
    chart_data = group_avg.pivot(index='year_month', columns='immigration_group', values=growth_col)

    logger.info(f"Created comparison: {HIGH_IMMIGRATION_LABEL} vs {OTHER_INDUSTRIES_LABEL}")

    # Convert index to datetime
    chart_data.index = pd.to_datetime(chart_data.index)
    chart_data = chart_data.sort_index()

    return chart_data


def create_rolling_average_data(chart_data, window=3):
    """Create 3-month rolling averages from chart data."""
    logger.info(f"Creating {window}-month rolling averages")

    rolling_data = chart_data.rolling(window=window, center=True).mean()

    return rolling_data


def create_employment_growth_chart(employment_df, session):
    """Create employment growth chart by immigration groups."""
    logger.info("Creating employment growth chart - High Immigration vs All Others")

    # Add immigration groups to data
    emp_with_groups = create_immigration_groups(employment_df)

    # Calculate averages by group
    chart_data = calculate_group_averages(
        emp_with_groups,
        'annualized_mom_employment_growth'
    )

    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(chart_data)

    # Apply GM formatting with consistent colors and font sizes
    gm_formatting(
        ax=ax,
        title=f"Employment Growth: {HIGH_IMMIGRATION_LABEL} vs {OTHER_INDUSTRIES_LABEL}\nAnnualized Month-over-Month Growth (Last 12 Months)",
        data=chart_data,
        color=['#4e81bd', '#cabd8f', '#505c54', '#003845', '#696a6d', 'black'],  # GM colors
        dateformat="%b-%y",  # Format like Jan-25
        ylabel="Employment Growth (%)",
        legend_ncol=2
    )

    # Increase font sizes for y-axis label and legend
    ax.yaxis.label.set_fontsize(14)
    legend = ax.get_legend()
    if legend:
        for text in legend.get_texts():
            text.set_fontsize(12)

    # Add horizontal line at 0
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

    chart_path = session.dir / "employment_growth_top10_immigration_vs_others.png"
    plt.savefig(chart_path, dpi=400, bbox_inches='tight')
    plt.close()

    logger.info(f"Employment growth chart saved to {chart_path}")

    # Save chart data
    data_path = session.dir / "employment_growth_top10_immigration_vs_others_data.csv"
    chart_data.to_csv(data_path)
    logger.info(f"Employment chart data saved to {data_path}")

    return chart_path


def create_employment_growth_rolling_chart(employment_df, session):
    """Create 3-month rolling average employment growth chart by immigration groups."""
    logger.info("Creating employment growth 3-month rolling average chart - High Immigration vs All Others")

    # Add immigration groups to data
    emp_with_groups = create_immigration_groups(employment_df)

    # Calculate averages by group
    chart_data = calculate_group_averages(
        emp_with_groups,
        'annualized_mom_employment_growth'
    )

    # Create 3-month rolling averages
    rolling_data = create_rolling_average_data(chart_data, window=3)

    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(rolling_data)

    # Apply GM formatting with consistent colors and font sizes
    gm_formatting(
        ax=ax,
        title=f"Employment Growth: {HIGH_IMMIGRATION_LABEL} vs {OTHER_INDUSTRIES_LABEL} (3-Month Rolling Average)\nAnnualized Month-over-Month Growth (Last 12 Months)",
        data=rolling_data,
        color=['#4e81bd', '#cabd8f', '#505c54', '#003845', '#696a6d', 'black'],  # GM colors
        dateformat="%b-%y",  # Format like Jan-25
        ylabel="Employment Growth (%) - 3-Month Average",
        legend_ncol=2
    )

    # Increase font sizes for y-axis label and legend
    ax.yaxis.label.set_fontsize(14)
    legend = ax.get_legend()
    if legend:
        for text in legend.get_texts():
            text.set_fontsize(12)

    # Add horizontal line at 0
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

    chart_path = session.dir / "employment_growth_top10_immigration_vs_others_rolling.png"
    plt.savefig(chart_path, dpi=400, bbox_inches='tight')
    plt.close()

    logger.info(f"Employment growth rolling average chart saved to {chart_path}")

    # Save chart data
    data_path = session.dir / "employment_growth_top10_immigration_vs_others_rolling_data.csv"
    rolling_data.to_csv(data_path)
    logger.info(f"Employment rolling average chart data saved to {data_path}")

    return chart_path


def create_earnings_growth_chart(earnings_df, session):
    """Create earnings growth chart by immigration groups."""
    logger.info("Creating earnings growth chart - High Immigration vs All Others")

    # Add immigration groups to data
    earn_with_groups = create_immigration_groups(earnings_df)

    # Calculate averages by group
    chart_data = calculate_group_averages(
        earn_with_groups,
        'annualized_mom_earnings_growth'
    )

    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(chart_data)

    # Apply GM formatting with consistent colors and font sizes
    gm_formatting(
        ax=ax,
        title=f"Earnings Growth: {HIGH_IMMIGRATION_LABEL} vs {OTHER_INDUSTRIES_LABEL}\nAnnualized Month-over-Month Growth (Last 12 Months)",
        data=chart_data,
        color=['#4e81bd', '#cabd8f', '#505c54', '#003845', '#696a6d', 'black'],  # GM colors
        dateformat="%b-%y",  # Format like Jan-25
        ylabel="Earnings Growth (%)",
        legend_ncol=2
    )

    # Increase font sizes for y-axis label and legend
    ax.yaxis.label.set_fontsize(14)
    legend = ax.get_legend()
    if legend:
        for text in legend.get_texts():
            text.set_fontsize(12)

    # Add horizontal line at 0
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

    chart_path = session.dir / "earnings_growth_top10_immigration_vs_others.png"
    plt.savefig(chart_path, dpi=400, bbox_inches='tight')
    plt.close()

    logger.info(f"Earnings growth chart saved to {chart_path}")

    # Save chart data
    data_path = session.dir / "earnings_growth_top10_immigration_vs_others_data.csv"
    chart_data.to_csv(data_path)
    logger.info(f"Earnings chart data saved to {data_path}")

    return chart_path


def create_earnings_growth_rolling_chart(earnings_df, session):
    """Create 3-month rolling average earnings growth chart by immigration groups."""
    logger.info("Creating earnings growth 3-month rolling average chart - High Immigration vs All Others")

    # Add immigration groups to data
    earn_with_groups = create_immigration_groups(earnings_df)

    # Calculate averages by group
    chart_data = calculate_group_averages(
        earn_with_groups,
        'annualized_mom_earnings_growth'
    )

    # Create 3-month rolling averages
    rolling_data = create_rolling_average_data(chart_data, window=3)

    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(rolling_data)

    # Apply GM formatting with consistent colors and font sizes
    gm_formatting(
        ax=ax,
        title=f"Earnings Growth: {HIGH_IMMIGRATION_LABEL} vs {OTHER_INDUSTRIES_LABEL} (3-Month Rolling Average)\nAnnualized Month-over-Month Growth (Last 12 Months)",
        data=rolling_data,
        color=['#4e81bd', '#cabd8f', '#505c54', '#003845', '#696a6d', 'black'],  # GM colors
        dateformat="%b-%y",  # Format like Jan-25
        ylabel="Earnings Growth (%) - 3-Month Average",
        legend_ncol=2
    )

    # Increase font sizes for y-axis label and legend
    ax.yaxis.label.set_fontsize(14)
    legend = ax.get_legend()
    if legend:
        for text in legend.get_texts():
            text.set_fontsize(12)

    # Add horizontal line at 0
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

    chart_path = session.dir / "earnings_growth_top10_immigration_vs_others_rolling.png"
    plt.savefig(chart_path, dpi=400, bbox_inches='tight')
    plt.close()

    logger.info(f"Earnings growth rolling average chart saved to {chart_path}")

    # Save chart data
    data_path = session.dir / "earnings_growth_top10_immigration_vs_others_rolling_data.csv"
    rolling_data.to_csv(data_path)
    logger.info(f"Earnings rolling average chart data saved to {data_path}")

    return chart_path


def create_employment_growth_combined_chart(employment_df, session):
    """Create combined employment growth chart with monthly data and rolling average."""
    logger.info("Creating combined employment growth chart - Monthly + Rolling Average")

    # Add immigration groups to data
    emp_with_groups = create_immigration_groups(employment_df)

    # Calculate monthly averages by group
    chart_data = calculate_group_averages(
        emp_with_groups,
        'annualized_mom_employment_growth'
    )

    # Create 3-month rolling averages
    rolling_data = create_rolling_average_data(chart_data, window=3)

    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot monthly data with thin lines
    for i, col in enumerate(chart_data.columns):
        color = ['#4e81bd', '#cabd8f', '#505c54', '#003845'][i % 4]
        # Map to simpler sector names
        sector_name = "High Immigration Sectors" if "Top 10%" in col else "All Other Sectors"
        ax.plot(chart_data.index, chart_data[col],
               linewidth=1.5, color=color, alpha=0.65,
               label=f'{sector_name}')

    # Plot rolling average with thick lines
    for i, col in enumerate(rolling_data.columns):
        color = ['#4e81bd', '#cabd8f', '#505c54', '#003845'][i % 4]
        # Map to simpler sector names
        sector_name = "High Immigration Sectors" if "Top 10%" in col else "All Other Sectors"
        ax.plot(rolling_data.index, rolling_data[col],
               linewidth=3.0, color=color,
               label=f'{sector_name} (3-Mo Average)')

    # Apply GM formatting (without automatic plotting)
    gm_formatting(
        ax=ax,
        title=None,  # No title for combined chart
        data=chart_data,  # Use chart_data for date formatting
        dateformat="%b-%y",  # Format like Jan-25
        ylabel="Employment Growth (%)",
        legend_ncol=2
    )

    # Manual legend setup for combined data
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
             frameon=False, ncol=2)

    # Increase font sizes for y-axis label and legend
    ax.yaxis.label.set_fontsize(14)
    legend = ax.get_legend()
    if legend:
        for text in legend.get_texts():
            text.set_fontsize(12)

    # Add horizontal line at 0
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

    chart_path = session.dir / "employment_growth_top10_immigration_vs_others_combined.png"
    plt.savefig(chart_path, dpi=400, bbox_inches='tight')
    plt.close()

    logger.info(f"Employment growth combined chart saved to {chart_path}")

    # Save chart data
    combined_data = chart_data.copy()
    for col in rolling_data.columns:
        combined_data[f'{col} (3-Mo Avg)'] = rolling_data[col]

    data_path = session.dir / "employment_growth_top10_immigration_vs_others_combined_data.csv"
    combined_data.to_csv(data_path)
    logger.info(f"Employment combined chart data saved to {data_path}")

    return chart_path


def create_earnings_growth_combined_chart(earnings_df, session):
    """Create combined earnings growth chart with monthly data and rolling average."""
    logger.info("Creating combined earnings growth chart - Monthly + Rolling Average")

    # Add immigration groups to data
    earn_with_groups = create_immigration_groups(earnings_df)

    # Calculate monthly averages by group
    chart_data = calculate_group_averages(
        earn_with_groups,
        'annualized_mom_earnings_growth'
    )

    # Create 3-month rolling averages
    rolling_data = create_rolling_average_data(chart_data, window=3)

    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot monthly data with thin lines
    for i, col in enumerate(chart_data.columns):
        color = ['#4e81bd', '#cabd8f', '#505c54', '#003845'][i % 4]
        # Map to simpler sector names
        sector_name = "High Immigration Sectors" if "Top 10%" in col else "All Other Sectors"
        ax.plot(chart_data.index, chart_data[col],
               linewidth=1.5, color=color, alpha=0.65,
               label=f'{sector_name}')

    # Plot rolling average with thick lines
    for i, col in enumerate(rolling_data.columns):
        color = ['#4e81bd', '#cabd8f', '#505c54', '#003845'][i % 4]
        # Map to simpler sector names
        sector_name = "High Immigration Sectors" if "Top 10%" in col else "All Other Sectors"
        ax.plot(rolling_data.index, rolling_data[col],
               linewidth=3.0, color=color,
               label=f'{sector_name} (3-Mo Average)')

    # Apply GM formatting (without automatic plotting)
    gm_formatting(
        ax=ax,
        title=None,  # No title for combined chart
        data=chart_data,  # Use chart_data for date formatting
        dateformat="%b-%y",  # Format like Jan-25
        ylabel="Earnings Growth (%)",
        legend_ncol=2
    )

    # Manual legend setup for combined data
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
             frameon=False, ncol=2)

    # Increase font sizes for y-axis label and legend
    ax.yaxis.label.set_fontsize(14)
    legend = ax.get_legend()
    if legend:
        for text in legend.get_texts():
            text.set_fontsize(12)

    # Add horizontal line at 0
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

    chart_path = session.dir / "earnings_growth_top10_immigration_vs_others_combined.png"
    plt.savefig(chart_path, dpi=400, bbox_inches='tight')
    plt.close()

    logger.info(f"Earnings growth combined chart saved to {chart_path}")

    # Save chart data
    combined_data = chart_data.copy()
    for col in rolling_data.columns:
        combined_data[f'{col} (3-Mo Avg)'] = rolling_data[col]

    data_path = session.dir / "earnings_growth_top10_immigration_vs_others_combined_data.csv"
    combined_data.to_csv(data_path)
    logger.info(f"Earnings combined chart data saved to {data_path}")

    return chart_path


def create_summary_statistics(employment_df, earnings_df, session):
    """Create summary statistics by immigration groups."""
    logger.info("Creating summary statistics by immigration groups")

    # Add immigration groups to both datasets
    emp_with_groups = create_immigration_groups(employment_df)
    earn_with_groups = create_immigration_groups(earnings_df)

    # Calculate overall average growth by group
    emp_summary = emp_with_groups.groupby('immigration_group').agg({
        'annualized_mom_employment_growth': ['mean', 'std', 'count'],
        'noncitizen_percentage': ['mean', 'min', 'max'],
        'industry_code': 'nunique'
    }).round(2)

    earn_summary = earn_with_groups.groupby('immigration_group').agg({
        'annualized_mom_earnings_growth': ['mean', 'std', 'count'],
        'noncitizen_percentage': ['mean', 'min', 'max'],
        'industry_code': 'nunique'
    }).round(2)

    # Flatten column names
    emp_summary.columns = ['_'.join(col).strip() for col in emp_summary.columns]
    earn_summary.columns = ['_'.join(col).strip() for col in earn_summary.columns]

    # Save summary statistics
    emp_summary_path = session.dir / "employment_growth_group_summary.csv"
    emp_summary.to_csv(emp_summary_path)
    logger.info(f"Employment summary statistics saved to {emp_summary_path}")

    earn_summary_path = session.dir / "earnings_growth_group_summary.csv"
    earn_summary.to_csv(earn_summary_path)
    logger.info(f"Earnings summary statistics saved to {earn_summary_path}")

    # Log key insights
    logger.info("=== KEY INSIGHTS ===")
    logger.info("Employment Growth by Immigration Group (Average %):")
    for group in emp_summary.index:
        avg_growth = emp_summary.loc[group, 'annualized_mom_employment_growth_mean']
        logger.info(f"  {group}: {avg_growth:.1f}%")

    logger.info("Earnings Growth by Immigration Group (Average %):")
    for group in earn_summary.index:
        avg_growth = earn_summary.loc[group, 'annualized_mom_earnings_growth_mean']
        logger.info(f"  {group}: {avg_growth:.1f}%")

    return emp_summary, earn_summary


def create_high_immigration_sectors_list(employment_df, session):
    """Create a CSV list of industries in the top immigration percentile."""
    logger.info("Creating high immigration sectors list")

    # Add immigration groups to data
    emp_with_groups = create_immigration_groups(employment_df)

    # Get unique industries with their immigration data
    industries_data = emp_with_groups.groupby(['industry_code', 'industry_name', 'immigration_group']).agg({
        'noncitizen_percentage': 'first',
        'total_workers': 'first',
        'noncitizen_workers': 'first'
    }).reset_index()

    # Filter for high immigration sectors only
    high_immigration_sectors = industries_data[
        industries_data['immigration_group'] == HIGH_IMMIGRATION_LABEL
    ].copy()

    # Sort by non-citizen percentage (descending)
    high_immigration_sectors = high_immigration_sectors.sort_values(
        'noncitizen_percentage', ascending=False
    ).reset_index(drop=True)

    # Add rank column
    high_immigration_sectors['rank'] = range(1, len(high_immigration_sectors) + 1)

    # Reorder columns for clarity
    output_columns = [
        'rank', 'industry_name', 'industry_code',
        'noncitizen_percentage', 'total_workers', 'noncitizen_workers'
    ]
    high_immigration_sectors = high_immigration_sectors[output_columns]

    # Round percentage for readability
    high_immigration_sectors['noncitizen_percentage'] = high_immigration_sectors['noncitizen_percentage'].round(2)

    # Save to CSV
    sectors_path = session.dir / "high_immigration_sectors_list.csv"
    high_immigration_sectors.to_csv(sectors_path, index=False)

    logger.info(f"High immigration sectors list saved to {sectors_path}")
    logger.info(f"Total sectors in top {(1-TOP_IMMIGRATION_PERCENTILE)*100:.0f}%: {len(high_immigration_sectors)}")

    # Log top 5 sectors
    logger.info("Top 5 high immigration sectors:")
    for _, row in high_immigration_sectors.head(5).iterrows():
        logger.info(f"  {row['rank']}. {row['industry_name']} ({row['noncitizen_percentage']:.2f}%)")

    return sectors_path


def create_employment_correlation_chart(employment_df, session):
    """Create correlation time series chart showing rolling correlation over time."""
    logger.info("Creating employment growth correlation time series chart - 3-month rolling averages")

    # Add immigration groups to data with 2-year lookback
    emp_with_groups = create_immigration_groups(employment_df)

    # Calculate group averages with 2-year lookback (24 months)
    chart_data = calculate_group_averages(
        emp_with_groups,
        'annualized_mom_employment_growth',
        lookback_months=24
    )

    # Create 3-month rolling averages
    rolling_data = create_rolling_average_data(chart_data, window=3)

    # Drop rows with NaN values (from rolling average calculation)
    rolling_data = rolling_data.dropna()

    # Extract the two series for correlation
    if HIGH_IMMIGRATION_LABEL in rolling_data.columns and OTHER_INDUSTRIES_LABEL in rolling_data.columns:
        high_immigration = rolling_data[HIGH_IMMIGRATION_LABEL]
        other_industries = rolling_data[OTHER_INDUSTRIES_LABEL]

        # Calculate rolling correlation (6-month window)
        # Create a combined DataFrame for easier correlation calculation
        combined_data = pd.DataFrame({
            'high_immigration': high_immigration,
            'other_industries': other_industries
        })

        # Calculate rolling correlation using a manual approach
        rolling_correlation = combined_data['high_immigration'].rolling(window=6, center=True).corr(combined_data['other_industries'])

        # Calculate overall correlation for reference
        overall_correlation = high_immigration.corr(other_industries)

        # Create line chart
        fig, ax = plt.subplots(figsize=(12, 8))

        # Plot rolling correlation line
        ax.plot(rolling_correlation.index, rolling_correlation.values,
               linewidth=3, color='#4e81bd', alpha=0.8)

        # Add horizontal reference line at 0 (no correlation)
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5, linewidth=1)

        # Add horizontal reference line at overall correlation
        ax.axhline(y=overall_correlation, color='#cabd8f', linestyle='--', alpha=0.7, linewidth=2,
                  label=f'Overall Correlation: {overall_correlation:.3f}')

        # Apply GM formatting
        gm_formatting(
            ax=ax,
            title=f"Employment Growth Correlation Over Time: High Immigration vs All Other Sectors\n6-Month Rolling Correlation of 3-Month Rolling Averages",
            data=rolling_correlation.to_frame('Correlation'),
            dateformat="%b-%y",
            ylabel="Correlation Coefficient",
            legend_ncol=1
        )

        # Increase font sizes
        ax.yaxis.label.set_fontsize(14)

        # Add custom legend
        ax.legend(['6-Month Rolling Correlation', f'Overall Correlation ({overall_correlation:.3f})'],
                 loc='upper center', bbox_to_anchor=(0.5, -0.1), frameon=False, ncol=2,
                 fontsize=12)

        # Set y-axis limits for better visualization
        ax.set_ylim(-1, 1)

        # Add grid for better readability
        ax.grid(True, alpha=0.3)

        chart_path = session.dir / "employment_growth_correlation_timeseries.png"
        plt.savefig(chart_path, dpi=400, bbox_inches='tight')
        plt.close()

        logger.info(f"Employment correlation time series chart saved to {chart_path}")
        logger.info(f"Overall correlation coefficient: {overall_correlation:.3f}")

        # Save correlation data
        correlation_data = pd.DataFrame({
            'date': rolling_data.index,
            'high_immigration_sectors': high_immigration,
            'all_other_sectors': other_industries,
            'rolling_correlation_6mo': rolling_correlation
        })
        correlation_data['overall_correlation'] = overall_correlation

        data_path = session.dir / "employment_growth_correlation_timeseries_data.csv"
        correlation_data.to_csv(data_path, index=False)
        logger.info(f"Correlation time series data saved to {data_path}")

        return chart_path

    else:
        logger.warning("Could not create correlation chart - required columns not found")
        return None


def main():
    """Analyze growth trends by immigration share quartiles and create visualizations."""
    logger.info("Starting immigration growth analysis")

    try:
        # Load data
        employment_df, earnings_df = load_analysis_data()

        # Create charts
        employment_chart = create_employment_growth_chart(employment_df, session)
        earnings_chart = create_earnings_growth_chart(earnings_df, session)

        # Create rolling average charts
        employment_rolling_chart = create_employment_growth_rolling_chart(employment_df, session)
        earnings_rolling_chart = create_earnings_growth_rolling_chart(earnings_df, session)

        # Create combined charts (monthly + rolling average)
        employment_combined_chart = create_employment_growth_combined_chart(employment_df, session)
        earnings_combined_chart = create_earnings_growth_combined_chart(earnings_df, session)

        # Create summary statistics
        emp_summary, earn_summary = create_summary_statistics(employment_df, earnings_df, session)

        # Create high immigration sectors list
        create_high_immigration_sectors_list(employment_df, session)

        # Create correlation analysis chart
        create_employment_correlation_chart(employment_df, session)

        # Log completion
        logger.info("=== ANALYSIS COMPLETE ===")
        logger.info(f"Output directory: {session.dir}")
        logger.info(f"Charts created: {employment_chart.name}, {earnings_chart.name}")
        logger.info(f"Rolling average charts created: {employment_rolling_chart.name}, {earnings_rolling_chart.name}")
        logger.info(f"Combined charts created: {employment_combined_chart.name}, {earnings_combined_chart.name}")
        logger.info(f"Charts show comparison between {HIGH_IMMIGRATION_LABEL} and {OTHER_INDUSTRIES_LABEL} (last 12 months)")
        logger.info("Summary statistics and data files saved")

        return True

    except Exception as e:
        logger.error(f"Immigration growth analysis failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
else:
    # Also run when imported from .qmd
    main()