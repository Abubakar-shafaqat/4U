"""
Shared utilities for Stealth MCQ Helper.

Contains logging functions and common helpers.
"""
import traceback
from datetime import datetime


def log(msg: str) -> None:
    """Print a timestamped log line."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {msg}", flush=True)


def log_error(context: str, error: Exception) -> None:
    """Log an error with context and traceback."""
    log(f"[ERROR] {context}: {type(error).__name__}: {error}")
    traceback.print_exc()