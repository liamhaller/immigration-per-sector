"""
BLS CPS and CES Data Fetcher for Breakeven Analysis

Downloads BLS Current Population Survey (CPS) and Current Employment Statistics (CES) 
data to raw data directory for breakeven rate analysis.
"""

from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import get_bls_dir, get_logger
from Tools.path_management import raw_data_dir

logger = get_logger(__name__)


def main():
    """Download BLS CPS (ln) and CES (ce) data to raw data directory."""
    logger.info('Starting BLS breakeven data download')
    
    try:
        # Download BLS Current Employment Statistics (ce series)
        logger.info('Downloading BLS CES data (ce series)')
        get_bls_dir(base_dir=str(raw_data_dir), code='ce')
        logger.info('BLS CES data download completed')
        
        logger.info('BLS breakeven data download completed successfully')

    except Exception as e:
        logger.error(f'BLS breakeven data download failed: {str(e)}')
        raise


if __name__ == "__main__":
    main()