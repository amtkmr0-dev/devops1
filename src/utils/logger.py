import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(log_level="INFO", log_file=None):
    """Setup application logging"""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Set log file
    if log_file is None:
        log_file = log_dir / "dividend_scanner.log"

    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
