"""Logging configuration for the application."""
import logging
import sys
import json
from typing import Any
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request ID if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class StandardFormatter(logging.Formatter):
    """Standard formatter with request ID support."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] [%(request_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with request ID."""
        if not hasattr(record, "request_id"):
            record.request_id = "N/A"
        return super().format(record)


def setup_logging(use_json: bool = False, level: str = "INFO") -> None:
    """Configure application logging.
    
    Args:
        use_json: If True, use JSON formatter. Otherwise use standard formatter.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Set formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = StandardFormatter()
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Set levels for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

