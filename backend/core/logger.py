"""
Centralized logging setup using loguru.
"""
import sys
import os
from loguru import logger

LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Remove default handler
logger.remove()

# Console handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

# File handler for all logs
logger.add(
    f"{LOG_DIR}/forest_guard.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# Separate error log
logger.add(
    f"{LOG_DIR}/errors.log",
    rotation="5 MB",
    retention="60 days",
    compression="zip",
    level="ERROR"
)


def get_logger(name: str = "forest_guard"):
    return logger.bind(module=name)
