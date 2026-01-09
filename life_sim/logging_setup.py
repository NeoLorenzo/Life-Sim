# life_sim/logging_setup.py
"""
Logging Configuration Module.
Sets up console and file logging based on config.
"""
import logging
import os
import sys
from datetime import datetime
from . import constants

def setup_logging(config: dict):
    """
    Configures the root logger.
    
    Args:
        config (dict): The loaded configuration dictionary.
    """
    log_level_str = config.get("logging", {}).get("level", "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # Create log directory if it doesn't exist
    if not os.path.exists(constants.LOG_DIR):
        os.makedirs(constants.LOG_DIR)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(constants.LOG_DIR, f"run_{timestamp}.log")
    
    # Format: Time | Level | Module | Message
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File Handler
    if config.get("logging", {}).get("save_to_file", True):
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
    logging.info(f"Logging initialized. Level: {log_level_str}")