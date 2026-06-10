"""
AIRA — Structured Logging
File + console handlers, colored dev output, JSON production format.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler


class ColoredFormatter(logging.Formatter):
    """Colored console output for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(app=None):
    """Configure application logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "./logs/aira.log")
    flask_env = os.getenv("FLASK_ENV", "development")

    # Create logger
    logger = logging.getLogger("aira")
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))

    if flask_env == "development":
        console_fmt = ColoredFormatter(
            "%(asctime)s │ %(levelname)s │ %(name)s │ %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        console_fmt = logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","message":"%(message)s"}'
        )

    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # File handler
    try:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        file_handler.setLevel(logging.INFO)
        file_fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        logger.warning(f"Could not create log file at {log_file}: {e}")

    # Attach to Flask app if provided
    if app:
        app.logger.handlers = logger.handlers
        app.logger.setLevel(logger.level)

    logger.info(f"AIRA Logger initialized [level={log_level}, env={flask_env}]")
    return logger


def get_logger(name="aira"):
    """Get a named child logger."""
    return logging.getLogger(f"aira.{name}")
