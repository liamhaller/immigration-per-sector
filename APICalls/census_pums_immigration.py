"""
Census PUMS (Public Use Microdata Sample) API Data Fetcher

Downloads Census PUMS data for immigration analysis by industry.
Fetches NAICSP (industry codes) and CIT (citizenship status) variables
with PWGTP (person weights) for calculating non-citizen shares by industry.
"""

from pathlib import Path
import sys
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import CachedAPIClient, raw_data_dir, census_api_key, get_logger

logger = get_logger(__name__)

# Initialize API client with longer cache for PUMS data (24 hours)
client = CachedAPIClient(cache_name="census_pums", cache_hours=24)

def main():
    """Download Census PUMS data for immigration by industry analysis."""

    logger.info('Starting Census PUMS data download for immigration analysis')

    try:
        # 2023 ACS 1-year PUMS data - national level
        # Variables:
        # - NAICSP: Industry code (NAICS) for person's job
        # - CIT: Citizenship status
        # - PWGTP: Person weight for population estimates

        base_url = "https://api.census.gov/data/2023/acs/acs1/pums"

        # Parameters for API call
        variables = "NAICSP,CIT,PWGTP"

        # Full URL - national level data (no geographic restriction)
        url = f"{base_url}?get={variables}&key={census_api_key}"

        logger.info(f"Fetching PUMS data from Census API")
        logger.info(f"Variables requested: {variables}")

        # Get data using cached client
        data = client.get_data(url)

        # Create output directory if it doesn't exist
        pums_dir = raw_data_dir / "census_pums"
        pums_dir.mkdir(parents=True, exist_ok=True)

        # Save raw data
        filepath = pums_dir / "pums_2023_immigration_industry.csv"
        data.to_csv(filepath, index=False)

        logger.info(f"Census PUMS data saved: {len(data):,} records to {filepath}")

        # Log basic data info
        logger.info(f"Data shape: {data.shape}")
        logger.info(f"Columns: {list(data.columns)}")

        return data

    except Exception as e:
        logger.error(f'Census PUMS data download failed: {str(e)}')
        raise


if __name__ == "__main__":
    main()
else:
    # Also run when imported from .qmd or main.py
    main()