import logging
import sys

def setup_logger(log_level: str = "INFO") -> None:
    """
    Configures a standardized structured console logger for the Transformer service.
    
    Args:
        log_level (str): Log verbosity threshold.
    """
    root_logger = logging.getLogger()
    
    if root_logger.hasHandlers():
        return
        
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
