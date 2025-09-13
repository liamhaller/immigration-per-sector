
"""
BLS Producer Price Index (PPI) API Data Fetcher

Downloads BLS PPI data to raw data directory.
"""

from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import bls_api_key, get_bls_dir, get_logger, raw_data_dir

logger = get_logger(__name__)


def main():
    """Download BLS PPI data to raw data directory."""
    logger.info('Starting BLS PPI data download')

    try:
        logger.info('Downloading most recent BLS PPI data')
        get_bls_dir(base_dir=str(raw_data_dir), code='pc')
        logger.info('BLS PPI data download completed successfully')

    except Exception as e:
        logger.error(f'BLS PPI data download failed: {str(e)}')
        raise




if __name__ == "__main__":
    main()
else:
    # Also run when imported from .qmd
    main()