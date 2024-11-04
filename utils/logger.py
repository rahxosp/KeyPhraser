import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from config import Config

class Logger:
    """Custom logger implementation"""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        """Initialize logger"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Create file handler if log file specified
        if log_file:
            log_path = Path(Config.DATA_DIR) / 'logs' / log_file
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
    
    @staticmethod
    def get_current_log_file() -> str:
        """Get log filename for current session"""
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"application_{timestamp}.log"
    
    def log_exception(self, exc: Exception):
        """Log exception with traceback"""
        self.logger.exception(f"An error occurred: {str(exc)}")
