"""
Helper method that generates a composite key based on doc_id and page_num.
"""
from logging import Logger

from utils import logging_config

logger: Logger = logging_config.get_logger(__name__)

# Use a large prime number for mixing
LARGE_PRIME = 15485863


def generate_composite_key(doc_id: int, page_num: int) -> int:
    """
    Static method that generates a composite key based on doc_id and page_num.

    Args:
        doc_id (int): The document ID.
        page_num (int): The page number.

    Returns:
        int: The generated composite key.
    """

    # Mix the doc_id and page_num using a prime number and bitwise XOR
    mixed_value = (doc_id * LARGE_PRIME) ^ page_num

    # Apply a modulus to ensure the result fits within a desired range
    composite_id = mixed_value % (10 ** 8)
    logger.debug("Composed IDs doc id: %d and page num %d: %d", doc_id, page_num, composite_id)

    return composite_id
