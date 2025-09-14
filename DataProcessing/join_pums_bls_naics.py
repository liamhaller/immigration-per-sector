"""
PUMS-BLS NAICS Code Mapping Module

Joins Census PUMS NAICS codes with BLS industry codes to enable
linking immigration data with BLS payroll data.

Maps NAICSP (Census PUMS) → naics_code (BLS) → industry_code (BLS)
"""

from pathlib import Path
import sys
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import get_logger, raw_data_dir, processed_data_dir

logger = get_logger(__name__)


def load_pums_data():
    """Load processed PUMS non-citizen data."""
    logger.info('Loading PUMS non-citizen data')

    pums_path = processed_data_dir / 'pums_noncitizen_by_industry.csv'
    logger.info(f'Loading PUMS data from {pums_path}')

    df = pd.read_csv(pums_path)
    logger.info(f'Loaded {len(df)} PUMS industry records')

    return df


def load_bls_industry_mapping():
    """Load BLS industry code mapping."""
    logger.info('Loading BLS industry code mapping')

    bls_industry_path = raw_data_dir / 'ce' / 'ce.industry.csv'
    logger.info(f'Loading BLS industry mapping from {bls_industry_path}')

    # Read with industry_code as string to prevent float conversion
    df = pd.read_csv(bls_industry_path, dtype={'industry_code': str})
    logger.info(f'Loaded {len(df)} BLS industry records')

    # Filter out records without NAICS codes (aggregated categories)
    df_with_naics = df[df['naics_code'] != '-'].copy()
    logger.info(f'Found {len(df_with_naics)} BLS records with NAICS codes')

    return df_with_naics


def clean_and_prepare_naics_codes(pums_df, bls_df):
    """Clean and prepare NAICS codes for matching."""
    logger.info('Cleaning and preparing NAICS codes for matching')

    # Clean PUMS NAICSP codes - convert to string and strip
    pums_df = pums_df.copy()
    pums_df['NAICSP_clean'] = pums_df['NAICSP'].astype(str).str.strip()

    # Clean BLS NAICS codes - handle complex codes with multiple NAICS
    bls_df = bls_df.copy()
    bls_df['naics_code_clean'] = bls_df['naics_code'].astype(str).str.strip()

    # Split BLS records that have multiple NAICS codes (comma-separated)
    # Example: "21221,3,9" becomes separate rows for 21221, 21223, 21229
    bls_expanded = []

    for _, row in bls_df.iterrows():
        naics_codes = row['naics_code_clean']

        if ',' in naics_codes:
            # Handle complex NAICS codes like "21221,3,9"
            parts = naics_codes.split(',')
            base_code = parts[0]

            # Add the base code
            new_row = row.copy()
            new_row['naics_code_clean'] = base_code
            bls_expanded.append(new_row)

            # Add variations by replacing last digit(s)
            for suffix in parts[1:]:
                if suffix.strip().isdigit():
                    # Replace last digit with suffix
                    if len(base_code) >= len(suffix.strip()):
                        variant_code = base_code[:-len(suffix.strip())] + suffix.strip()
                        new_row = row.copy()
                        new_row['naics_code_clean'] = variant_code
                        bls_expanded.append(new_row)
        else:
            # Single NAICS code
            bls_expanded.append(row)

    bls_expanded_df = pd.DataFrame(bls_expanded)
    logger.info(f'Expanded BLS data to {len(bls_expanded_df)} records after handling multi-NAICS codes')

    return pums_df, bls_expanded_df


def join_pums_bls_naics(pums_df, bls_df):
    """Join PUMS data with BLS industry codes via NAICS."""
    logger.info('Joining PUMS data with BLS industry codes')

    # Perform the join
    joined_df = pums_df.merge(
        bls_df[['naics_code_clean', 'industry_code', 'industry_name', 'display_level', 'publishing_status']],
        left_on='NAICSP_clean',
        right_on='naics_code_clean',
        how='left'
    )

    # Log matching statistics
    total_pums = len(pums_df)
    matched = joined_df['industry_code'].notna().sum()
    unmatched = total_pums - matched

    logger.info(f'Matching results:')
    logger.info(f'  Total PUMS industries: {total_pums}')
    logger.info(f'  Matched with BLS: {matched} ({matched/total_pums*100:.1f}%)')
    logger.info(f'  Unmatched: {unmatched} ({unmatched/total_pums*100:.1f}%)')

    if unmatched > 0:
        logger.info('Sample unmatched NAICS codes:')
        unmatched_codes = joined_df[joined_df['industry_code'].isna()]['NAICSP_clean'].head(10)
        for code in unmatched_codes:
            total_workers = pums_df[pums_df['NAICSP_clean'] == code]['total_workers'].iloc[0]
            logger.info(f'  {code} ({total_workers:,.0f} workers)')

    # Log top matched industries
    logger.info('Top 5 matched industries by worker count:')
    matched_df = joined_df[joined_df['industry_code'].notna()].sort_values('total_workers', ascending=False)
    for _, row in matched_df.head().iterrows():
        logger.info(f'  {row["NAICSP_clean"]} → {row["industry_code"]}: {row["industry_name"]} ({row["total_workers"]:,.0f} workers)')

    return joined_df


def save_joined_data(joined_df):
    """Save the joined PUMS-BLS data."""
    logger.info('Saving joined PUMS-BLS data')

    # Ensure processed directory exists
    processed_data_dir.mkdir(exist_ok=True)

    # Save complete joined dataset
    output_path = processed_data_dir / 'pums_bls_naics_joined.csv'
    joined_df.to_csv(output_path, index=False)
    logger.info(f'Saved joined data to {output_path}')

    # Save matched records only
    matched_df = joined_df[joined_df['industry_code'].notna()].copy()
    matched_path = processed_data_dir / 'pums_bls_naics_matched.csv'
    matched_df.to_csv(matched_path, index=False)
    logger.info(f'Saved matched data to {matched_path} ({len(matched_df)} records)')


def main():
    """Join PUMS NAICS codes with BLS industry codes."""
    logger.info("Starting PUMS-BLS NAICS code joining")

    try:
        # Load data
        pums_df = load_pums_data()
        bls_df = load_bls_industry_mapping()

        # Clean and prepare codes
        pums_clean, bls_clean = clean_and_prepare_naics_codes(pums_df, bls_df)

        # Join the data
        joined_df = join_pums_bls_naics(pums_clean, bls_clean)

        # Save results
        save_joined_data(joined_df)

        logger.info("PUMS-BLS NAICS code joining completed successfully")
        return True

    except Exception as e:
        logger.error(f"PUMS-BLS NAICS code joining failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()