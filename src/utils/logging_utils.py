"""
Logging Utility Functions
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration
    
    Args:
        log_level (int): Logging level (default: INFO)
        log_file (str, optional): Path to log file
    """
    # Create logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Create formatters
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # Set up file handler if log_file is provided
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
    
    # Log setup information
    logging.info(f"Logging initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Log level: {logging.getLevelName(log_level)}")
    if log_file:
        logging.info(f"Log file: {log_file}")

def get_logger(name: str, log_level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger with a specific name
    
    Args:
        name (str): Logger name
        log_level (int, optional): Specific log level for this logger
        
    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(name)
    
    if log_level is not None:
        logger.setLevel(log_level)
    
    return logger