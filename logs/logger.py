# sponsor_match/utils/logger.py
import logging
import os

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Set up a logger with both file and console handlers

    Args:
        name: Logger name (usually __name__ from calling module)
        log_file: Optional log file path
        level: Logging level

    Returns:
        Configured logger instance
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
