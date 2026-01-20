"""
Logging configuration for the Hindi Voice Assistant.
"""
import logging
import logging.handlers
import os

def setup_logging(
    level: int = logging.INFO,
    log_file: str = "assistant.log",
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 3
) -> logging.Logger:
    """
    Configure and return the root logger.
    
    Args:
        level: Logging level (e.g., logging.INFO).
        log_file: Path to the log file.
        max_bytes: Max size before rotation.
        backup_count: Number of backup logs to keep.
        
    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # File Handler (Rolling)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific component."""
    return logging.getLogger(name)
