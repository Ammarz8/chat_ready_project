import logging
import sys

def setup_logger(log_level: str = "INFO") -> None:
    """
    Configures a standardized structured console logger for the ETL services.
    
    Args:
        log_level (str): Log verbosity threshold (DEBUG, INFO, WARNING, ERROR).
    """
    root_logger = logging.getLogger()
    
    # Check if handlers already exist to prevent duplicate log printings
    if root_logger.hasHandlers():
        return
        
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Standard output handler (stdout) for container logs extraction
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set default external libraries to WARNING to keep log files clean
    logging.getLogger("urllib3").setLevel(logging.WARNING)
