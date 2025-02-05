"""
Author: Anton Pastoriza
"""
import time
import urllib
from logging import Logger

import requests
from requests import RequestException, Response

from urllib.parse import quote

from utils import logging_config

logger: Logger = logging_config.get_logger(__name__)


def get(host: str, endpoint: str, retries: int = 15, delay: int = 2) -> dict:
    """
    Sends a GET request to the specified host and endpoint, and returns the parsed JSON response as a dictionary.

    Parameters:
    host (str): The hostname of the server.
    endpoint (str): The endpoint of the RESTful service.

    Returns:
    dict: The parsed JSON response as a dictionary if successful.
    None: If the request fails or the response is not valid JSON.
    """
    # Initialize an empty dictionary to store the response data
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    url: str = f"{host}{endpoint}"
    data_dict: dict = invoke_get(url, retries, delay)
    logger.debug("Result from host='%s', endpoint='%s': %s", host, endpoint, data_dict)
    return data_dict


def invoke_get(url: str, retries: int = 15, delay: int = 2) -> dict:
    """
    Sends a GET request to the specified URL and returns the parsed JSON response as a dictionary.

    Parameters:
    url (str): The URL of the RESTful service.

    Returns:
    dict: The parsed JSON response as a dictionary if successful.
    None: If the request fails or the response is not valid JSON.
    """
    # Initialize an empty dictionary to store the response data
    data_dict: dict = {}
    total_retries: int = 0
    got_response: bool = False
    logger.info("Loading data from '%s'", url)

    while not got_response and total_retries < retries:
        try:
            response: Response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Parse and return the JSON response
            data_dict = response.json()
            logger.debug("Result from '%s': %s", url, data_dict)
            got_response = True

        except ConnectionError as e:
            logger.error("Connection refused: %s", e)
        except RequestException as e:
            logger.error("HTTP exception occurred: %s", e)
        except ValueError:
            logger.error("Failed to decode JSON response.")
        except Exception as e:
            logger.error("An unexpected error occurred: %s", e)

        total_retries += 1
        if not got_response and total_retries < retries - 1:
            logger.info("Retrying '%s' in %d seconds...", url, delay)
            time.sleep(delay)

    return data_dict


def invoke_post(url: str, parameters: dict, retries: int = 15, delay: int = 2) -> dict:
    data_dict: dict = {}
    total_retries: int = 0
    got_response: bool = False

    headers: dict[str, str] = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    logger.info("Posting data to '%s': %s", url, parameters)
    while not got_response and total_retries < retries:
        try:
            response: Response = requests.post(
                url,
                headers=headers,
                json=parameters
            )
            response.raise_for_status()
            data_dict = response.json()
            got_response = True
        except ConnectionError as e:
            logger.error("Connection refused: %s", e)
        except RequestException as e:
            logger.error("HTTP exception occurred: %s", e)
        except ValueError:
            logger.error("Failed to decode JSON response.")
        except Exception as e:
            logger.error("An unexpected error occurred: %s", e)

        total_retries += 1
        if not got_response and total_retries < retries - 1:
            logger.info("Retrying '%s' in %d seconds...", url, delay)
            time.sleep(delay)

    return data_dict


def compose_url(template: str, params: dict) -> str:
    # Encode each parameter value
    encoded_params = {key: urllib.parse.quote(str(value)) for key, value in params.items()}

    # Use str.format to replace the placeholders with the encoded values
    final_url = template.format(**encoded_params)

    return final_url
