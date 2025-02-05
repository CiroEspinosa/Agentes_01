"""
Author: Anton Pastoriza
"""


import logging
import sys
from logging import Logger


def get_logger(name: str, level=logging.INFO) -> Logger:
    """
    Get a configured logger instance. If the logger does not have handlers attached,
    it sets up basic configuration to log messages to the standard output.

    Args:
        name (str): The name of the logger. Typically, this would be the module's `__name__`.
        level (int): The logging level, e.g., logging.INFO, logging.DEBUG. Defaults to logging.INFO.

    Returns:
        Logger: A configured logger instance.
    """
    logger: Logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    return logger
