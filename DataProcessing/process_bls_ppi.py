"""
BLS Producer Price Index (PPI) Data Processing Module

Processes BLS PPI data for three-digit NAICS sectors.
Loads, filters, cleans and saves processed PPI data.
"""

from pathlib import Path
import sys
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import get_logger, raw_data_dir, processed_data_dir

logger = get_logger(__name__)


def load_and_filter_ppi_data():
    """Load PPI data and filter for three-digit NAICS codes."""
    logger.info('Filtering PPI data for three-digit codes')

    ppi_data_path = raw_data_dir / 'pc' / 'pc.data.0.Current.csv'
    logger.info(f'Loading PPI data from {ppi_data_path}')
    df = pd.read_csv(ppi_data_path)

    # Filter for series with three-digit codes (PCU###---###--- pattern)
    three_digit_pattern = r'^PCU(\d{3})---\1---'
    three_digit_ppi = df[df['series_id'].str.match(three_digit_pattern, na=False)]

    logger.info(f"Found {three_digit_ppi['series_id'].nunique()} unique three-digit PPI series")
    return three_digit_ppi


def process_ppi_data(three_digit_ppi):
    """Process and clean PPI data for analysis."""
    logger.info('Processing and cleaning PPI data')

    # Filter for year >= 2015
    initial_rows = len(three_digit_ppi)
    three_digit_ppi = three_digit_ppi[three_digit_ppi['year'] >= 2015].copy()
    logger.info(f'Filtered to years >= 2015: {len(three_digit_ppi)} rows (removed {initial_rows - len(three_digit_ppi)} older records)')

    # Create time column (YYYY-MM format to match import_naics)
    three_digit_ppi['month'] = three_digit_ppi['period'].str.extract(r'M(\d{2})')[0]
    # Filter out M13 (annual average) - only keep monthly data M01-M12
    valid_months = three_digit_ppi['month'].astype(int).between(1, 12)
    before_monthly = len(three_digit_ppi)
    three_digit_ppi = three_digit_ppi[valid_months].copy()
    logger.info(f'Filtered to monthly data (M01-M12): {len(three_digit_ppi)} rows (removed {before_monthly - len(three_digit_ppi)} annual averages)')

    three_digit_ppi['time'] = three_digit_ppi['year'].astype(str) + '-' + three_digit_ppi['month']

    # Create NAICS column (extract three-digit code from series_id)
    three_digit_ppi['NAICS'] = three_digit_ppi['series_id'].str.extract(r'PCU(\d{3})---')[0]

    # Keep only required columns (drop series_id, year, period, footnote_codes, Unnamed: 0)
    three_digit_ppi = three_digit_ppi[['time', 'NAICS', 'value']]
    logger.info('Data processing completed - final columns: time, NAICS, value')

    return three_digit_ppi


def save_processed_data(three_digit_ppi):
    """Save processed PPI data to processed directory."""
    logger.info('Saving processed data')

    # Ensure processed directory exists
    processed_data_dir.mkdir(exist_ok=True)
    logger.info(f'Ensured processed directory exists: {processed_data_dir}')

    # Save processed data
    output_path = processed_data_dir / 'three_digit_ppi.csv'
    three_digit_ppi.to_csv(output_path, index=False)
    logger.info(f"Saved {len(three_digit_ppi)} rows to {output_path}")


def main():
    """Process PPI data for three-digit NAICS sectors."""
    logger.info("Starting BLS PPI data processing")

    try:
        three_digit_ppi = load_and_filter_ppi_data()
        processed_ppi = process_ppi_data(three_digit_ppi)
        save_processed_data(processed_ppi)

        logger.info("BLS PPI data processing completed successfully")
        return True

    except Exception as e:
        logger.error(f"BLS PPI data processing failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()