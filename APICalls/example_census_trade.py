
import pandas as pd
from pathlib import Path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import CachedAPIClient, raw_data_dir, census_api_key, get_logger

logger = get_logger(__name__)


# Initialize API client
client = CachedAPIClient(cache_name="import_naics", cache_hours=1)

# Cache management examples:
#client.clear_old_cache(days_old=0)  # Clear all cache
#client.clear_old_cache(days_old=7)  # Clear cache older than 7 days
#print(client.get_cache_info())      # Show cache statistics

def main():
    # Generate dynamic date range (2 years and 5 months back to current month)
    current_date = pd.Timestamp.now()
    end_date = current_date.strftime('%Y-%m')
    start_date = (current_date - pd.DateOffset(years=2, months=5)).strftime('%Y-%m')

    logger.info(f"Fetching import NAICS data from {start_date} to {end_date}")

    # Download NAICS Data
    end_use_url = f'https://api.census.gov/data/timeseries/intltrade/imports/naics?get=CAL_DUT_MO,CON_VAL_MO,CTY_NAME,DUT_VAL_MO,NAICS,NAICS_SDESC&time=from+{start_date}+to+{end_date}&COMM_LVL=NA3&CTY_CODE=-'

    # Get data and save
    data = client.get_data(end_use_url)
    filepath = raw_data_dir / "import_naics.csv"
    data.to_csv(filepath, index=False)
    logger.info(f"Import NAICS data saved: {len(data)} records to {filepath}")

# Execute when imported or run directly
if __name__ == "__main__":
    main()
else:
    # Also run when imported from .qmd
    main()