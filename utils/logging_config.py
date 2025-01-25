# utils/logging_config.py

import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure application-wide logging"""
    # Create logs directory in user's home directory
    log_dir = os.path.join(os.path.expanduser('~'), '.magnetic_observatory', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log filename with timestamp
    log_file = os.path.join(
        log_dir, 
        f'magnetic_observatory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Create and configure file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log initial information
    logger.info("Logging system initialized")
    logger.info(f"Log file: {log_file}")
    
    return logger

def get_logger(name):
    """Get a logger instance for a specific module"""
    return logging.getLogger(name)