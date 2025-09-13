"""
Centralized Logging Configuration

Provides consistent logging setup across the entire project.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import inspect


def setup_logging(level=logging.INFO, log_to_file=True, log_file=None):
    """
    Configure logging for the project.
    
    Parameters:
    -----------
    level : int
        Logging level (default: logging.INFO)
    log_to_file : bool
        Whether to also log to a file (default: True)
    log_file : str or Path
        Path to log file (default: auto-generated based on calling script)
    """
    
    # Configure basic logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Add file handler if requested
    if log_to_file:
        if log_file is None:
            # Auto-generate log file name based on calling script
            project_root = Path(__file__).parent.parent
            log_dir = project_root / 'Output' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Get the calling script name
            frame = inspect.currentframe()
            try:
                # Go up the call stack to find the main script
                caller_frame = frame.f_back
                while caller_frame and caller_frame.f_code.co_filename.endswith('util_logging.py'):
                    caller_frame = caller_frame.f_back
                
                if caller_frame:
                    caller_file = Path(caller_frame.f_code.co_filename).stem
                else:
                    caller_file = "unknown_script"
            finally:
                del frame
            
            # Create timestamped log file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"{caller_file}_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(file_handler)
        
        # Log the file location for reference
        logging.getLogger(__name__).info(f"Logging to file: {log_file}")


def get_logger(name):
    """
    Get a logger instance for a module.
    
    Parameters:
    -----------
    name : str
        Logger name (typically __name__)
        
    Returns:
    --------
    logging.Logger
        Configured logger instance
    """
    return logging.getLogger(name)


# Configure logging when this module is imported
setup_logging()