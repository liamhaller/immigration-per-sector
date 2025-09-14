"""
BLS Employment & Earnings Analysis with Immigration Shares

Creates two datasets linking BLS employment/earnings trends with immigration shares
for matched industries from Jan 2023 to latest available data.
Calculates annualized month-over-month growth rates using seasonally adjusted data.
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import get_logger, raw_data_dir, processed_data_dir

logger = get_logger(__name__)


def load_matched_data():
    """Load the matched PUMS-BLS data."""
    logger.info('Loading matched PUMS-BLS data')

    matched_path = processed_data_dir / 'pums_bls_naics_matched.csv'
    matched_df = pd.read_csv(matched_path)

    logger.info(f'Loaded {len(matched_df)} matched industries')
    return matched_df


def load_bls_series_data():
    """Load BLS series and main data files."""
    logger.info('Loading BLS series and data files')

    # Load series mapping
    series_path = raw_data_dir / 'ce' / 'ce.series.csv'
    series_df = pd.read_csv(series_path, dtype={'industry_code': str})
    logger.info(f'Loaded {len(series_df)} BLS series')

    # Load main data file
    data_path = raw_data_dir / 'ce' / 'ce.data.0.AllCESSeries.csv'
    data_df = pd.read_csv(data_path)
    logger.info(f'Loaded {len(data_df)} BLS data records')

    return series_df, data_df


def generate_series_ids(matched_df, series_df):
    """Generate BLS series IDs for employment and earnings data."""
    logger.info('Generating BLS series IDs for matched industries')

    # Filter for seasonally adjusted series with data types 01 (employment) and 03 (earnings)
    # Convert data_type_code to string for comparison since it may be stored as string
    employment_series = series_df[(series_df['data_type_code'].astype(str) == '01') & (series_df['seasonal'] == 'S')].copy()
    earnings_series = series_df[(series_df['data_type_code'].astype(str) == '03') & (series_df['seasonal'] == 'S')].copy()

    logger.info(f'Found {len(employment_series)} employment series and {len(earnings_series)} earnings series')

    # Create mapping for matched industries
    industry_series_map = []
    supersector_conflicts = []

    for _, row in matched_df.iterrows():
        industry_code = str(row['industry_code'])  # Ensure string comparison
        industry_name = row['industry_name']
        noncitizen_pct = row['noncitizen_percentage']
        total_workers = row['total_workers']
        noncitizen_workers = row['noncitizen_workers']

        # Find employment series (convert both to string for comparison)
        emp_matches = employment_series[employment_series['industry_code'].astype(str) == industry_code]
        earn_matches = earnings_series[earnings_series['industry_code'].astype(str) == industry_code]

        # Check for supersector conflicts
        if len(emp_matches) > 1:
            supersector_conflicts.append(f"Employment: {industry_code} matches {len(emp_matches)} supersectors")
        if len(earn_matches) > 1:
            supersector_conflicts.append(f"Earnings: {industry_code} matches {len(earn_matches)} supersectors")

        # Take first match if multiple (should be rare)
        emp_series_id = emp_matches.iloc[0]['series_id'].strip() if len(emp_matches) > 0 else None
        earn_series_id = earn_matches.iloc[0]['series_id'].strip() if len(earn_matches) > 0 else None

        if emp_series_id or earn_series_id:
            industry_series_map.append({
                'industry_code': industry_code,
                'industry_name': industry_name,
                'employment_series_id': emp_series_id,
                'earnings_series_id': earn_series_id,
                'noncitizen_percentage': noncitizen_pct,
                'total_workers': total_workers,
                'noncitizen_workers': noncitizen_workers
            })

    # Log conflicts if any
    if supersector_conflicts:
        logger.warning(f'Found {len(supersector_conflicts)} supersector conflicts:')
        for conflict in supersector_conflicts:
            logger.warning(f'  {conflict}')

    series_map_df = pd.DataFrame(industry_series_map)
    logger.info(f'Generated series mapping for {len(series_map_df)} industries')
    if not series_map_df.empty:
        logger.info(f'  Employment series available: {series_map_df["employment_series_id"].notna().sum()}')
        logger.info(f'  Earnings series available: {series_map_df["earnings_series_id"].notna().sum()}')
    else:
        logger.warning('No series mapping data generated')

    return series_map_df


def filter_time_series_data(data_df, start_date='2023-01'):
    """Filter BLS data for the specified time period."""
    logger.info(f'Filtering BLS data from {start_date} onwards')

    # Convert year and period to datetime for filtering
    data_df = data_df.copy()
    data_df['year_month'] = data_df['year'].astype(str) + '-' + data_df['period'].str.replace('M', '').str.zfill(2)

    # Filter for time period
    filtered_df = data_df[data_df['year_month'] >= start_date].copy()

    logger.info(f'Filtered to {len(filtered_df)} records from {start_date} onwards')
    return filtered_df


def calculate_growth_rates(data_df, series_ids, value_col='value'):
    """Calculate annualized month-over-month growth rates."""
    logger.info('Calculating annualized month-over-month growth rates')

    # Filter for relevant series
    series_data = data_df[data_df['series_id'].str.strip().isin(series_ids)].copy()

    if len(series_data) == 0:
        logger.warning('No data found for provided series IDs')
        return pd.DataFrame()

    # Sort by series and date
    series_data = series_data.sort_values(['series_id', 'year', 'period'])

    # Calculate growth rates
    growth_data = []

    for series_id in series_data['series_id'].str.strip().unique():
        series_subset = series_data[series_data['series_id'].str.strip() == series_id].copy()

        # Calculate month-over-month change
        series_subset['prev_value'] = series_subset[value_col].shift(1)
        series_subset['mom_growth'] = (series_subset[value_col] / series_subset['prev_value']) - 1

        # Convert to annualized rate: (1 + mom_growth)^12 - 1
        series_subset['annualized_mom_growth'] = ((1 + series_subset['mom_growth']) ** 12 - 1) * 100

        # Remove first row (no previous value for growth calculation)
        series_subset = series_subset[series_subset['prev_value'].notna()]

        growth_data.append(series_subset)

    if growth_data:
        growth_df = pd.concat(growth_data, ignore_index=True)
        logger.info(f'Calculated growth rates for {len(growth_df)} data points')
        return growth_df
    else:
        return pd.DataFrame()


def create_employment_analysis(series_map_df, data_df):
    """Create employment analysis dataset."""
    logger.info('Creating employment analysis dataset')

    # Get employment series IDs
    emp_series_ids = series_map_df[series_map_df['employment_series_id'].notna()]['employment_series_id'].tolist()

    if not emp_series_ids:
        logger.error('No employment series IDs found')
        return pd.DataFrame()

    # Calculate growth rates
    emp_growth_df = calculate_growth_rates(data_df, emp_series_ids)

    if emp_growth_df.empty:
        logger.error('No employment growth data calculated')
        return pd.DataFrame()

    # Merge with immigration data
    employment_analysis = emp_growth_df.merge(
        series_map_df[['employment_series_id', 'industry_code', 'industry_name',
                      'noncitizen_percentage', 'total_workers', 'noncitizen_workers']],
        left_on=emp_growth_df['series_id'].str.strip(),
        right_on='employment_series_id',
        how='inner'
    )

    # Clean up and rename columns
    employment_analysis = employment_analysis[[
        'industry_code', 'industry_name', 'year_month', 'value',
        'annualized_mom_growth', 'noncitizen_percentage', 'total_workers', 'noncitizen_workers'
    ]].copy()

    employment_analysis.rename(columns={
        'value': 'employment_level',
        'annualized_mom_growth': 'annualized_mom_employment_growth'
    }, inplace=True)

    logger.info(f'Created employment analysis with {len(employment_analysis)} records')
    return employment_analysis


def create_earnings_analysis(series_map_df, data_df):
    """Create earnings analysis dataset."""
    logger.info('Creating earnings analysis dataset')

    # Get earnings series IDs
    earn_series_ids = series_map_df[series_map_df['earnings_series_id'].notna()]['earnings_series_id'].tolist()

    if not earn_series_ids:
        logger.error('No earnings series IDs found')
        return pd.DataFrame()

    # Calculate growth rates
    earn_growth_df = calculate_growth_rates(data_df, earn_series_ids)

    if earn_growth_df.empty:
        logger.error('No earnings growth data calculated')
        return pd.DataFrame()

    # Merge with immigration data
    earnings_analysis = earn_growth_df.merge(
        series_map_df[['earnings_series_id', 'industry_code', 'industry_name',
                      'noncitizen_percentage', 'total_workers', 'noncitizen_workers']],
        left_on=earn_growth_df['series_id'].str.strip(),
        right_on='earnings_series_id',
        how='inner'
    )

    # Clean up and rename columns
    earnings_analysis = earnings_analysis[[
        'industry_code', 'industry_name', 'year_month', 'value',
        'annualized_mom_growth', 'noncitizen_percentage', 'total_workers', 'noncitizen_workers'
    ]].copy()

    earnings_analysis.rename(columns={
        'value': 'avg_hourly_earnings',
        'annualized_mom_growth': 'annualized_mom_earnings_growth'
    }, inplace=True)

    logger.info(f'Created earnings analysis with {len(earnings_analysis)} records')
    return earnings_analysis


def validate_growth_rates(df, growth_col, threshold=200):
    """Validate growth rates and flag extreme values."""
    if growth_col not in df.columns:
        return df

    extreme_values = df[abs(df[growth_col]) > threshold]
    if len(extreme_values) > 0:
        logger.warning(f'Found {len(extreme_values)} extreme growth rate values (>{threshold}% annualized):')
        for _, row in extreme_values.head(10).iterrows():
            logger.warning(f'  {row.get("industry_name", "Unknown")}: {row[growth_col]:.1f}% in {row.get("year_month", "Unknown")}')

    return df


def save_analysis_data(employment_df, earnings_df):
    """Save the analysis datasets."""
    logger.info('Saving analysis datasets')

    # Ensure processed directory exists
    processed_data_dir.mkdir(exist_ok=True)

    # Save employment analysis
    if not employment_df.empty:
        emp_path = processed_data_dir / 'employment_immigration_analysis.csv'
        employment_df.to_csv(emp_path, index=False)
        logger.info(f'Saved employment analysis to {emp_path} ({len(employment_df)} records)')

    # Save earnings analysis
    if not earnings_df.empty:
        earn_path = processed_data_dir / 'earnings_immigration_analysis.csv'
        earnings_df.to_csv(earn_path, index=False)
        logger.info(f'Saved earnings analysis to {earn_path} ({len(earnings_df)} records)')


def main():
    """Create BLS employment and earnings analysis with immigration shares."""
    logger.info("Starting BLS employment and earnings immigration analysis")

    try:
        # Load matched data
        matched_df = load_matched_data()

        # Load BLS data
        series_df, data_df = load_bls_series_data()

        # Generate series IDs for matched industries
        series_map_df = generate_series_ids(matched_df, series_df)

        # Filter time series data from Jan 2023
        filtered_data_df = filter_time_series_data(data_df, '2023-01')

        # Create employment analysis
        employment_analysis = create_employment_analysis(series_map_df, filtered_data_df)
        employment_analysis = validate_growth_rates(employment_analysis, 'annualized_mom_employment_growth')

        # Create earnings analysis
        earnings_analysis = create_earnings_analysis(series_map_df, filtered_data_df)
        earnings_analysis = validate_growth_rates(earnings_analysis, 'annualized_mom_earnings_growth')

        # Save results
        save_analysis_data(employment_analysis, earnings_analysis)

        # Summary statistics
        logger.info("Analysis Summary:")
        logger.info(f"  Employment dataset: {len(employment_analysis)} records")
        logger.info(f"  Earnings dataset: {len(earnings_analysis)} records")
        if not employment_analysis.empty:
            logger.info(f"  Date range: {employment_analysis['year_month'].min()} to {employment_analysis['year_month'].max()}")
            logger.info(f"  Industries with employment data: {employment_analysis['industry_code'].nunique()}")
        if not earnings_analysis.empty:
            logger.info(f"  Industries with earnings data: {earnings_analysis['industry_code'].nunique()}")

        logger.info("BLS employment and earnings immigration analysis completed successfully")
        return True

    except Exception as e:
        logger.error(f"BLS employment and earnings immigration analysis failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()