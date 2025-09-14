"""
Census PUMS Immigration Data Processing Module

Processes Census PUMS data to calculate non-citizen shares by industry.
Computes weighted worker counts by citizenship status and industry,
then calculates the percentage of non-citizens in each industry.

CIT Variable Codes (Citizenship Status):
1 = Born in US
2 = Born in Puerto Rico
3 = Born abroad to US citizen
4 = US citizen by naturalization
5 = Not a US citizen
"""

from pathlib import Path
import sys
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import get_logger, raw_data_dir, processed_data_dir

logger = get_logger(__name__)


def load_pums_data():
    """Load Census PUMS data from raw directory."""
    logger.info('Loading Census PUMS data')

    pums_data_path = raw_data_dir / 'census_pums' / 'pums_2023_immigration_industry.csv'
    logger.info(f'Loading PUMS data from {pums_data_path}')

    df = pd.read_csv(pums_data_path)
    logger.info(f'Loaded {len(df):,} records with columns: {list(df.columns)}')

    return df


def clean_and_filter_data(df):
    """Clean and filter PUMS data for analysis."""
    logger.info('Cleaning and filtering PUMS data')

    initial_rows = len(df)

    # Remove records with missing industry codes (NAICSP)
    df_clean = df[df['NAICSP'].notna()].copy()
    logger.info(f'Removed {initial_rows - len(df_clean):,} records with missing NAICSP')

    # Remove records with missing citizenship status
    df_clean = df_clean[df_clean['CIT'].notna()].copy()
    logger.info(f'Remaining records after removing missing CIT: {len(df_clean):,}')

    # Remove records with missing or zero weights
    df_clean = df_clean[(df_clean['PWGTP'].notna()) & (df_clean['PWGTP'] > 0)].copy()
    logger.info(f'Remaining records after removing invalid weights: {len(df_clean):,}')

    # Convert data types
    df_clean['NAICSP'] = df_clean['NAICSP'].astype(str)
    df_clean['CIT'] = df_clean['CIT'].astype(int)
    df_clean['PWGTP'] = df_clean['PWGTP'].astype(float)

    # Log citizenship distribution
    logger.info('Citizenship status distribution:')
    cit_labels = {
        1: 'Born in US',
        2: 'Born in Puerto Rico',
        3: 'Born abroad to US citizen',
        4: 'US citizen by naturalization',
        5: 'Not a US citizen'
    }

    for cit_code in sorted(df_clean['CIT'].unique()):
        count = (df_clean['CIT'] == cit_code).sum()
        weighted_count = df_clean[df_clean['CIT'] == cit_code]['PWGTP'].sum()
        label = cit_labels.get(cit_code, f'Unknown ({cit_code})')
        logger.info(f'  {cit_code} ({label}): {count:,} records, {weighted_count:,.0f} weighted')

    return df_clean


def calculate_industry_citizenship_totals(df):
    """Calculate weighted worker counts by industry and citizenship status."""
    logger.info('Calculating weighted worker counts by industry and citizenship')

    # Group by industry and citizenship, sum the weights
    industry_citizenship_long = df.groupby(['NAICSP', 'CIT'])['PWGTP'].sum().reset_index()
    industry_citizenship_long.columns = ['NAICSP', 'CIT', 'weighted_workers']

    # Create citizenship category labels
    cit_labels = {
        1: 'Born_in_US',
        2: 'Born_in_Puerto_Rico',
        3: 'Born_abroad_to_US_citizen',
        4: 'US_citizen_by_naturalization',
        5: 'Not_a_US_citizen'
    }
    industry_citizenship_long['citizenship_status'] = industry_citizenship_long['CIT'].map(cit_labels)

    # Pivot to have citizenship status as columns and NAICS as rows
    industry_citizenship = industry_citizenship_long.pivot_table(
        index='NAICSP',
        columns='citizenship_status',
        values='weighted_workers',
        fill_value=0
    ).reset_index()

    # Flatten column names
    industry_citizenship.columns.name = None

    # Calculate total workers by industry
    industry_totals = df.groupby('NAICSP')['PWGTP'].sum().reset_index()
    industry_totals.columns = ['NAICSP', 'total_workers']

    logger.info(f'Calculated totals for {len(industry_totals)} industries')

    return industry_citizenship, industry_totals


def calculate_noncitizen_percentages(industry_citizenship, industry_totals):
    """Calculate the percentage of non-citizens in each industry."""
    logger.info('Calculating non-citizen percentages by industry')

    # Extract non-citizen workers from the pivoted table
    noncitizen_column = 'Not_a_US_citizen'
    if noncitizen_column in industry_citizenship.columns:
        noncitizen_totals = industry_citizenship[['NAICSP', noncitizen_column]].copy()
        noncitizen_totals.columns = ['NAICSP', 'noncitizen_workers']
    else:
        # If no non-citizens exist, create empty dataframe
        noncitizen_totals = industry_citizenship[['NAICSP']].copy()
        noncitizen_totals['noncitizen_workers'] = 0

    # Merge with industry totals
    industry_analysis = industry_totals.merge(noncitizen_totals, on='NAICSP', how='left')

    # Fill missing non-citizen counts with 0
    industry_analysis['noncitizen_workers'] = industry_analysis['noncitizen_workers'].fillna(0)

    # Calculate percentage
    industry_analysis['noncitizen_percentage'] = (industry_analysis['noncitizen_workers'] / industry_analysis['total_workers']) * 100

    # Sort by non-citizen percentage descending
    industry_analysis = industry_analysis.sort_values('noncitizen_percentage', ascending=False)

    logger.info(f'Calculated non-citizen percentages for {len(industry_analysis)} industries')
    logger.info(f'Top 5 industries by non-citizen percentage:')
    for _, row in industry_analysis.head().iterrows():
        logger.info(f'  {row["NAICSP"]}: {row["noncitizen_percentage"]:.1f}% ({row["noncitizen_workers"]:,.0f}/{row["total_workers"]:,.0f})')

    return industry_analysis


def save_processed_data(industry_citizenship, industry_analysis):
    """Save processed data to processed directory."""
    logger.info('Saving processed data')

    # Ensure processed directory exists
    processed_data_dir.mkdir(exist_ok=True)
    logger.info(f'Ensured processed directory exists: {processed_data_dir}')

    # Save detailed industry-citizenship breakdown
    detailed_path = processed_data_dir / 'pums_industry_citizenship_detail.csv'
    industry_citizenship.to_csv(detailed_path, index=False)
    logger.info(f'Saved detailed breakdown to {detailed_path}')

    # Save industry analysis with non-citizen percentages
    analysis_path = processed_data_dir / 'pums_noncitizen_by_industry.csv'
    industry_analysis.to_csv(analysis_path, index=False)
    logger.info(f'Saved industry analysis to {analysis_path}')


def main():
    """Process Census PUMS data for immigration by industry analysis."""
    logger.info("Starting Census PUMS immigration data processing")

    try:
        # Load data
        df = load_pums_data()

        # Clean and filter
        df_clean = clean_and_filter_data(df)

        # Calculate totals
        industry_citizenship, industry_totals = calculate_industry_citizenship_totals(df_clean)

        # Calculate non-citizen percentages
        industry_analysis = calculate_noncitizen_percentages(industry_citizenship, industry_totals)

        # Save results
        save_processed_data(industry_citizenship, industry_analysis)

        logger.info("Census PUMS immigration data processing completed successfully")
        return True

    except Exception as e:
        logger.error(f"Census PUMS immigration data processing failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()