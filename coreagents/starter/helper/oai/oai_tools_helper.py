"""
Author: Anton Pastoriza
"""
import time
from logging import Logger

import jsonref
import requests
from requests import RequestException, Response

from utils import logging_config

logger: Logger = logging_config.get_logger(__name__)


def generate_tool_functions(swagger_url: str, retries: int = 50, delay: int = 2) -> dict[str, dict[str, list[dict]]]:
    """
    Fetches and processes a Swagger/OpenAPI specification from a given URL, generating a list of tool functions ready
    for OpenAI completion based on the API paths and methods defined in the specification.

    The function makes repeated attempts to fetch the OpenAPI specification, with a configurable number of retries
    and delay between each retry. If successful, the specification is parsed, and tool functions are generated
    based on the API paths, methods, and their respective parameters.

    Args:
        swagger_url (str): The URL where the Swagger/OpenAPI specification is hosted.
        retries (int, optional): The maximum number of retries for fetching the OpenAPI specification. Default is 15.
        delay (int, optional): The delay (in seconds) between retries if the request fails. Default is 2 seconds.

    Returns:
        dict[str, dict[str, list[dict]]]: For every path and HTTP method, the list of dictionaries representing the
        generated tool functions, where each function includes its name, description, and parameters extracted from the
        OpenAPI specification.

    Raises:
        ConnectionError: If the connection to the URL is refused.
        RequestException: If an HTTP error occurs during the request.
        ValueError: If the JSON response cannot be decoded.
        Exception: If an unexpected error occurs during the process.

    Notes:
        - The function logs errors and retries the request up to the specified number of retries.
        - It uses `jsonref` to resolve JSON references within the OpenAPI specification.
        - The generated functions are based on the `operationId`, `description`, and `parameters` of each
          API operation in the specification.
    """
    functions: dict[str, dict[str, list[dict]]] = {}
    total_retries: int = 0
    got_response: bool = False
    while not got_response and total_retries < retries:
        try:
            response: Response = requests.get(swagger_url)
            response.raise_for_status()  # This will raise an exception for HTTP errors
            # Load the JSON content with jsonref
            openapi_spec: dict = jsonref.loads(response.text)
            functions = openapi_to_functions(openapi_spec)
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
            logger.info("Retrying '%s' in %d seconds...", swagger_url, delay)
            time.sleep(delay)

    return functions


def openapi_to_functions(openapi_spec: dict) -> dict[str, dict[str, list[dict]]]:
    """
    Converts an OpenAPI specification into a list of tool functions, each represented as a dictionary.

    The function processes the paths and methods defined in the OpenAPI specification, extracting relevant
    information such as the function name (`operationId`), description, and parameters. The parameters
    are structured into a JSON schema format.

    Args:
        openapi_spec (dict): The OpenAPI specification dictionary, typically loaded from a JSON file or URL.

    Returns:
        dict[str, list[dict]]: For every path, the list of dictionaries, each representing a tool function. Each function dictionary contains:
                    - 'name': The name of the function, derived from `operationId`.
                    - 'description': A brief description or summary of the function.
                    - 'parameters': A schema defining the parameters required by the function, including both
                                    request bodies and query/path parameters.

    Notes:
        - The function assumes the OpenAPI specification follows the standard structure, with `paths`
          containing the operations and their metadata.
        - The JSON references within the OpenAPI specification are resolved using `jsonref`.
        - The output content is something like:
            'http://tool_financinglines:7105/financing/creditAndLending/{customer}': {
                'get': [{
                    'type': 'function',
                    'function': {
                        'name': 'get_financing_lines_financing_creditAndLending__customer__get',
                        'description': 'Endpoint to get the financing lines of a corporate customer',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'parameters': {
                                    'type': 'object',
                                    'properties': {
                                        'customer': {
                                            'type': 'string',
                                            'title': 'Customer'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }]
            }
    """
    endpoint_functions: dict[str, dict[str, list[dict]]] = {}
    for path, methods in openapi_spec["paths"].items():
        endpoint_functions[path] = {}
        logger.debug("Interacting path '%s'", path)
        for method, spec_with_ref in methods.items():
            if method not in endpoint_functions:
                endpoint_functions[path][method] = []
            logger.debug("Interacting '%s' / '%s'", path, method)
            # 1. Resolve JSON references.
            spec = jsonref.replace_refs(spec_with_ref)

            # 2. Extract a name for the functions.
            function_name = spec.get("operationId")

            # 3. Extract a description and parameters.
            desc = spec.get("description") or spec.get("summary", "")

            schema = {
                "type": "object",
                "properties": {}
            }

            req_body = (
                spec.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema")
            )
            if req_body:
                schema["properties"]["requestBody"] = req_body

            params = spec.get("parameters", [])
            if params:
                param_properties = {}
                for param in params:
                    if "schema" in param:
                        param_properties[param["name"]] = param["schema"]

                schema["properties"]["parameters"] = {
                    "type": "object",
                    "properties": param_properties,
                }

            endpoint_functions[path][method].append({
                "type": "function",
                "function": {
                    "name": function_name,
                    "description": desc,
                    "parameters": schema
                }
            })
    logger.debug("Generated structured OpenAPI spec tools: %s", endpoint_functions)
    return endpoint_functions
