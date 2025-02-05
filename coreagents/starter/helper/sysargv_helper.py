"""
This module provides utility functions to retrieve and process command-line arguments with logging support.

The module includes functions to retrieve command-line parameters as either strings or integers,
with the ability to specify default values in case the parameters are missing or invalid.
Warnings are logged if the expected parameters are not provided or cannot be converted to the desired type.

Author: Anton Pastoriza
"""

import sys
from logging import Logger

from utils import logging_config

logger: Logger = logging_config.get_logger(__name__)


def retrieve_parameter_as_str(position: int, parameter_name: str, default_value: str = "") -> str:
    """
    Retrieves a command-line argument as a string based on its position in `sys.argv`.
    If the argument is not provided, a default value is returned, and a warning is logged.

    Args:
        position (int): The position of the desired argument in `sys.argv`.
        parameter_name (str): The name of the parameter to use in logging messages.
        default_value (str, optional): The default value to return if the argument is not provided.
                                       Defaults to an empty string.

    Returns:
        str: The value of the command-line argument at the specified position,
             or the default value if the argument is not provided.

    Logs:
        Warning: Logs a warning if the argument is not provided or if the default value is used.
    """
    value: str = default_value
    if len(sys.argv) > position:
        value = sys.argv[position]
    else:
        logger.warning(f"Starting agent: No {parameter_name} provided. Using default value '{value}'.")
    return value


def retrieve_parameter_as_int(position: int, parameter_name: str, default_value: int = 0) -> int:
    """
    Retrieves a command-line argument as an integer based on its position in `sys.argv`.
    If the argument is not provided or cannot be converted to an integer, a default value is returned,
    and a warning is logged.

    Args:
        position (int): The position of the desired argument in `sys.argv`.
        parameter_name (str): The name of the parameter to use in logging messages.
        default_value (int, optional): The default value to return if the argument is not provided
                                       or is not a valid integer. Defaults to 0.

    Returns:
        int: The value of the command-line argument at the specified position converted to an integer,
             or the default value if the argument is not provided or cannot be converted to an integer.

    Logs:
        Warning: Logs a warning if the argument is not provided, is not a valid integer,
                 or if the default value is used.
    """
    value: int = default_value
    if len(sys.argv) > position:
        try:
            value: int = int(sys.argv[position])
        except ValueError:
            logger.warning(f"Starting agent: Invalid {parameter_name} value provided: {sys.argv[position]}. Using default value: {value}.")
    else:
        logger.warning(f"Starting agent: No {parameter_name} provided. Using default value {default_value}.")
    return value
