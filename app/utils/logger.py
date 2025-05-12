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
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))

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
        json_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Use JSON format for file logs and plain text for console logs
        console_handler.setFormatter(log_format)
        file_handler.setFormatter(json_format)

        # Add handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        # Add module and function name to log records
        class ContextFilter(logging.Filter):
            def filter(self, record):
                record.module = record.module if hasattr(record, 'module') else 'unknown'
                record.funcName = record.funcName if hasattr(record, 'funcName') else 'unknown'
                return True

        context_filter = ContextFilter()
        self.logger.addFilter(context_filter)

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

    def log_metric(self, metric_name, value, tags=None):
        """Log a metric for monitoring purposes"""
        metric = {
            "metric_name": metric_name,
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.now().isoformat()
        }
        self.logger.info(f"Metric logged: {metric}")

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
