"""
Configuration and Path Management

Central configuration file for managing project paths and common imports
used across different analysis modules.
"""

from pathlib import Path



# Project structure paths
project_root = Path(__file__).parent.parent
data_dir = project_root / 'data'
processed_data_dir = data_dir / 'processed'
raw_data_dir = data_dir / 'raw'



# Module directories
APICalls_dir = project_root / 'APICalls'
DataProcessing_dir = project_root / 'DataProcessing'
Analysis_dir = project_root / 'Analysis'
Tools_dir = project_root / 'Tools'
assets_dir = Tools_dir / 'assets'
Output_dir = project_root / 'output'

