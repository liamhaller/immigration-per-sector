from pathlib import Path
import sys
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import get_bea_dir, raw_data_dir, get_logger

logger = get_logger(__name__)


def main():
    # WARNING: BEA has strict rate limits and will temporarily block your IP
    # if you make too many calls too quickly. Always use delays between calls.

    logger.info("Downloading PCE data from BEA API...")
    pce_data = get_bea_dir(table='T20804', dataset='NIPA')
    pce_data.to_csv(raw_data_dir / "bea_pce_data.csv", index=False)
    logger.info(f"BEA PCE data saved: {len(pce_data)} records")

    logger.info("Waiting 60 seconds between API calls to respect rate limits...")
    time.sleep(60)

    logger.info("Downloading PCE prices from BEA API...")
    pce_prices = get_bea_dir(table='T20404', dataset='NIUnderlyingDetail')
    pce_prices.to_csv(raw_data_dir / "bea_pce_prices.csv", index=False)
    logger.info(f"BEA PCE prices saved: {len(pce_prices)} records")

# Execute when imported or run directly
if __name__ == "__main__":
    main()
else:
    # Also run when imported from .qmd
    main()