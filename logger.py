import logging
import os
from datetime import datetime
import traceback
import sys
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Log file paths
APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOGS_DIR, "error.log")
ACCESS_LOG_FILE = os.path.join(LOGS_DIR, "access.log")

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Create formatters
standard_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
detailed_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(standard_formatter)
root_logger.addHandler(console_handler)

# App log file handler (rotating)
app_file_handler = RotatingFileHandler(
    APP_LOG_FILE, maxBytes=10*1024*1024, backupCount=5
)
app_file_handler.setLevel(logging.INFO)
app_file_handler.setFormatter(standard_formatter)
root_logger.addHandler(app_file_handler)

# Error log file handler (rotating)
error_file_handler = RotatingFileHandler(
    ERROR_LOG_FILE, maxBytes=10*1024*1024, backupCount=5
)
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(detailed_formatter)
root_logger.addHandler(error_file_handler)

# Access logger (separate logger for access logs)
access_logger = logging.getLogger("access")
access_logger.setLevel(logging.INFO)
access_logger.propagate = False  # Don't propagate to root logger

access_file_handler = RotatingFileHandler(
    ACCESS_LOG_FILE, maxBytes=10*1024*1024, backupCount=5
)
access_file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(message)s'
))
access_logger.addHandler(access_file_handler)

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def log_access(user_id, endpoint, method="GET", status_code=200):
    """Log an API/page access"""
    access_logger.info(f"User: {user_id} - Method: {method} - Endpoint: {endpoint} - Status: {status_code}")

def log_error(error, context=None):
    """Log an error with context and stack trace"""
    logger = get_logger("error")
    error_message = str(error)
    stack_trace = traceback.format_exc()
    
    context_str = ""
    if context:
        context_str = " - Context: " + str(context)
    
    logger.error(f"Error: {error_message}{context_str}\nStack Trace: {stack_trace}")

def log_chat(user_id, query, response, model_used):
    """Log a chat interaction"""
    logger = get_logger("chat")
    logger.info(f"User: {user_id} - Model: {model_used} - Query: {query[:50]}... - Response: {response[:50]}...")

def log_api_call(api_name, success, duration_ms, error=None):
    """Log an external API call"""
    logger = get_logger("api")
    status = "Success" if success else "Failed"
    error_msg = f" - Error: {error}" if error else ""
    logger.info(f"API: {api_name} - Status: {status} - Duration: {duration_ms}ms{error_msg}")

class ErrorHandler:
    """Context manager for handling and logging errors"""
    
    def __init__(self, context=None, reraise=True):
        """
        Initialize error handler
        
        Parameters:
        - context: Context information for the error
        - reraise: Whether to reraise the exception after logging
        """
        self.context = context
        self.reraise = reraise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            log_error(exc_val, self.context)
            return not self.reraise
        return False
