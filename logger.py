import logging
import os
from datetime import datetime

def setup_logger():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create logs directory
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Setup logger
    logger = logging.getLogger('InstaReview')
    
    # Only setup if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create file handler with timestamp
        log_file = os.path.join(logs_dir, f"feedback_processing_{timestamp}.log")
        file_handler = logging.FileHandler(log_file)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger, timestamp

def create_categorical_folders():
    """Create categorical folders for organized storage"""
    folders = {
        'data': "data",
        'reports': "reports",
        'logs': "logs"
    }
    
    for folder in folders.values():
        os.makedirs(folder, exist_ok=True)
    
    return folders