"""
US Census Manufacturer's Shipments Inventories & Orders Data

Fetches monthly manufacturing data from 2018 to June 2025
for all available NAICS codes using the M3 dataset.
"""

import pandas as pd
from pathlib import Path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from Tools import CachedAPIClient, raw_data_dir, census_api_key, get_logger

logger = get_logger(__name__)


# Initialize API client
client = CachedAPIClient(cache_name="manufacturing", cache_hours=8)

# Cache management examples:
#client.clear_old_cache(days_old=0)  # Clear all cache
#client.clear_old_cache(days_old=7)  # Clear cache older than 7 days
#print(client.get_cache_info())      # Show cache statistics

# Configuration
start_year = "1995"
end_date = "2025-06"
base_url = "https://api.census.gov/data/timeseries/eits/m3"

def build_api_url(base_url, data_type_code, time_range):
    """Build Census API URL for manufacturing data."""
    return f"{base_url}?get=cell_value,time_slot_id,error_data,category_code,seasonally_adj,data_type_code,time_slot_date,time_slot_name&for=US&seasonally_adj=no&data_type_code={data_type_code}&time={time_range}&key={census_api_key}"

def fetch_manufacturing_data(data_type, url):
    """Fetch data from Census API."""
    logger.info(f"Fetching manufacturing {data_type} data...")
    data = client.get_data(url)
    logger.info(f"Manufacturing {data_type} data: {len(data)} records")
    return data

def clean_data(data):
    """Clean and format manufacturing data."""
    if 'cell_value' in data.columns:
        data['cell_value'] = pd.to_numeric(data['cell_value'], errors='coerce')
    if 'time_slot_date' in data.columns:
        data['time_slot_date'] = pd.to_datetime(data['time_slot_date'], errors='coerce')
    return data

def save_data(data, filename):
    """Save data to CSV file."""
    filepath = raw_data_dir / filename
    data.to_csv(filepath, index=False)
    logger.info(f"Data saved to: {filepath}")

def main():
    # Build time range from configuration
    time_range = f"from+{start_year}+to+{end_date}"

    # Fetch inventories data
    inventories_url = build_api_url(base_url, "TI", time_range)
    inventories_data = fetch_manufacturing_data("total inventories", inventories_url)
    inventories_data = clean_data(inventories_data)
    save_data(inventories_data, "manufacturing_inventories.csv")

    # Fetch shipments data
    shipments_url = build_api_url(base_url, "VS", time_range)
    shipments_data = fetch_manufacturing_data("value of shipments", shipments_url)
    shipments_data = clean_data(shipments_data)
    save_data(shipments_data, "manufacturing_shipments.csv")

# Execute when imported or run directly
if __name__ == "__main__":
    main()
else:
    # Also run when imported from .qmd
    main()

