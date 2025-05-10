import logging
import os
from datetime import datetime

class VulnLearnAILogger:
    def __init__(self):
        self.logger = None
        self.setup_logging()

    def setup_logging(self):
        """Initialize logging configuration"""
        # Create logs directory if it doesn't exist
        os.makedirs("data/logs", exist_ok=True)

        # Create logger
        self.logger = logging.getLogger("VulnLearnAI")
        self.logger.setLevel(logging.INFO)

        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(
            f"data/logs/vulnlearnai_{datetime.now().strftime('%Y%m%d')}.log"
        )

        # Create formatters and add it to handlers
        log_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(log_format)
        file_handler.setFormatter(log_format)

        # Add handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def info(self, message):
        """Log info level message"""
        if self.logger:
            self.logger.info(message)

    def error(self, message):
        """Log error level message"""
        if self.logger:
            self.logger.error(message)

    def warning(self, message):
        """Log warning level message"""
        if self.logger:
            self.logger.warning(message)

    def debug(self, message):
        """Log debug level message"""
        if self.logger:
            self.logger.debug(message)

# Create global logger instance
logger = VulnLearnAILogger()

# Export common logging functions
def log_info(message):
    logger.info(message)

def log_error(message):
    logger.error(message)

def log_warning(message):
    logger.warning(message)

def log_debug(message):
    logger.debug(message)
