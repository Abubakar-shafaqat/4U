"""
Logging configuration for Stealth MCQ Helper.

Provides file and console logging with rotation.
"""
import logging
import logging.handlers
from pathlib import Path

from config import CONFIG


def setup_logging(config=None) -> logging.Logger:
    """
    Set up logging based on configuration.
    
    Args:
        config: Optional LoggingConfig. Uses global CONFIG if not provided.
        
    Returns:
        Configured logger instance.
    """
    if config is None:
        config = CONFIG.logging
    
    logger = logging.getLogger("4Utool")
    logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if config.console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if config.file:
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "app.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Global logger instance
_logger = None

def get_logger() -> logging.Logger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


def log(msg: str) -> None:
    """Log an info message."""
    get_logger().info(msg)


def log_error(context: str, error: Exception) -> None:
    """Log an error with context and traceback."""
    import traceback
    get_logger().error(f"{context}: {type(error).__name__}: {error}")
    get_logger().debug(traceback.format_exc())