"""
Date and time helper functions

Author: Anton Pastoriza
"""

from datetime import datetime


def timestamp_now_as_str() -> str:
    """
    Get the current timestamp and convert it to a formatted string.

    Returns:
        str: The current timestamp in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    timestamp: datetime = datetime.now()
    return timestamp_as_str(timestamp)


def timestamp_as_str(timestamp: datetime) -> str:
    """
    Convert a datetime object to a string in the format 'YYYY-MM-DD HH:MM:SS'.

    Args:
        timestamp (datetime): A datetime object to be converted to a string.

    Returns:
        str: The formatted string representation of the datetime object.
    """
    # Convert datetime object to string
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return timestamp_str
