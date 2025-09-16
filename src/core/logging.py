import os
import sys

from loguru import logger

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")


def setup_logger():
    logger.remove()

    logger.add(
        sys.stdout,
        colorize=True,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        level="INFO",
        enqueue=True,
    )

    return logger
