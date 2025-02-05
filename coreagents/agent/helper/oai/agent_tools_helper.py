"""
This module provides functionality to compose tools and execute HTTP calls
based on tool calls using the OpenAI API's chat completion tools.

Author: Anton Pastoriza
"""
import json
from logging import Logger
from typing import Optional

from openai.types.chat import ChatCompletionMessageToolCall

from utils import logging_config, http_invoker_helper

logger: Logger = logging_config.get_logger(__name__)


def compose_tools(tools: dict[str, dict[str, list[dict]]]) -> list[dict]:
    """
    Composes a list of tools from a nested dictionary of HTTP endpoints and their associated methods.

    Args:
        tools (dict): A dictionary where keys are HTTP endpoints, and values are dictionaries mapping HTTP methods
                      to lists of tool definitions.

    Returns:
        list: A list of tool definitions aggregated from the provided dictionary.
    """
    logger.debug("Current agent tools: %s", tools)
    agent_tools: list[dict] = []
    # Iterate over the http_endpoint and its corresponding methods dictionary
    for http_endpoint, methods_dict in tools.items():
        # Iterate over the HTTP methods ('get', 'post', etc.) and their associated tool definitions
        for http_method, method_tools in methods_dict.items():
            logger.debug("Retrieving tools for '%s' - '%s': %s", http_endpoint, http_method, method_tools)
            agent_tools.extend(method_tools)
    return agent_tools


def execute_call_from_tools(tools: dict[str, dict[str, list[dict]]], tool_call: ChatCompletionMessageToolCall) -> dict:
    """
    Executes an HTTP call based on a tool call definition.

    Args:
        tools (dict): A dictionary where keys are HTTP endpoints, and values are dictionaries mapping HTTP methods
                      to lists of tool definitions.
        tool_call (ChatCompletionMessageToolCall): The tool call object containing the details of the tool to execute.

    Returns:
        dict: The response from the executed HTTP call.
    """
    logger.info("Called tool id: '%s', name: '%s', arguments: '%s'", tool_call.id, tool_call.function.name, tool_call.function.arguments)
    http_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    response: dict = {}

    http_endpoint, http_method = _retrieve_http_request_values(tools, tool_call.function.name)
    if http_endpoint is not None and http_method is not None:
        if http_method.upper() == "GET":
            parameters: dict = _retrieve_parameters_from_tool_call_function(tool_call.function.arguments)
            logger.info("Parameters for tool id: '%s', name: '%s': %s", tool_call.id, tool_call.function.name, parameters)
            response = _execute_get(http_endpoint, parameters)
        elif http_method.upper() == "POST":
            request_body: dict = _retrieve_request_body_from_tool_call_function(tool_call.function.arguments)
            logger.info("Request body for tool id: '%s', name: '%s': %s", tool_call.id, tool_call.function.name, request_body)
            response = _execute_post(http_endpoint, request_body)
        else:
            logger.error("Invalid http method '%s' for '%s'", http_method.upper(), http_endpoint)

    return response


def _execute_get(http_endpoint: str, parameters: dict) -> dict:
    """
    Executes a GET request to the specified HTTP endpoint with the provided parameters.

    Args:
        http_endpoint (str): The endpoint to send the GET request to.
        parameters (dict): A dictionary of parameters to include in the GET request.

    Returns:
        dict: The response from the GET request.
    """
    logger.debug("Getting http endpoint for '%s'", http_endpoint)
    url: str = http_invoker_helper.compose_url(http_endpoint, parameters)
    logger.info("Getting for http endpoint '%s'", url)
    response: dict = http_invoker_helper.invoke_get(url)
    logger.info("Response for http endpoint '%s': %s", url, response)
    return response


def _execute_post(http_endpoint: str, request_body: dict) -> dict:
    """
    Executes a POST request to the specified HTTP endpoint with the provided request body.

    Args:
        http_endpoint (str): The endpoint to send the POST request to.
        request_body (dict): A dictionary representing the body of the POST request.

    Returns:
        dict: The response from the POST request.
    """
    logger.debug("Posting http endpoint for '%s'", http_endpoint)
    response: dict = http_invoker_helper.invoke_post(http_endpoint, request_body)
    logger.info("Response for http endpoint '%s': %s", http_endpoint, response)
    return response


def _retrieve_parameters_from_tool_call_function(tool_call_function_arguments: str) -> dict:
    """
    Retrieves the parameters from the tool call function arguments.

    Args:
        tool_call_function_arguments (str): The JSON string representing the arguments passed to the tool function.

    Returns:
        dict: A dictionary of parameters extracted from the tool call function arguments.
    """
    return _retrieve_arguments_from_tool_call_function("parameters", tool_call_function_arguments)


def _retrieve_request_body_from_tool_call_function(tool_call_function_arguments: str) -> dict:
    """
    Retrieves the request body from the tool call function arguments.

    Args:
        tool_call_function_arguments (str): The JSON string representing the arguments passed to the tool function.

    Returns:
        dict: A dictionary representing the request body extracted from the tool call function arguments.
    """
    return _retrieve_arguments_from_tool_call_function("requestBody", tool_call_function_arguments)


def _retrieve_arguments_from_tool_call_function(key_argument: str, tool_call_function_arguments: str) -> dict:
    """
    Retrieves specific arguments (parameters or request body) from the tool call function arguments.

    Args:
        key_argument (str): The key to retrieve ('parameters' or 'requestBody').
        tool_call_function_arguments (str): The JSON string representing the arguments passed to the tool function.

    Returns:
        dict: A dictionary of the specified arguments extracted from the tool call function arguments.
    """
    parameters: dict = {}
    if tool_call_function_arguments:
        arguments = json.loads(tool_call_function_arguments)
        if arguments:
            parameters = arguments.get(key_argument, {})
    return parameters


def _retrieve_http_request_values(tools, tool_call_function_name: str) -> Optional[tuple[str, str]]:
    """
    Retrieves the HTTP endpoint and method associated with a given tool call function name.

    Args:
        tools (dict): A dictionary where keys are HTTP endpoints, and values are dictionaries mapping HTTP methods
                      to lists of tool definitions.
        tool_call_function_name (str): The name of the tool function to locate.

    Returns:
        Optional[tuple[str, str]]: A tuple containing the HTTP endpoint and method if found, otherwise (None, None).
    """
    found: bool = False
    http_endpoint: Optional[str] = None
    http_method: Optional[str] = None

    # Iterate over the http_endpoint and its corresponding methods dictionary
    http_endpoints: list[tuple[str, dict[str, list[dict]]]] = list(tools.items())
    i: int = 0
    while not found and i < len(http_endpoints):
        methods_dict: Optional[dict[str, list[dict]]] = None
        http_endpoint, methods_dict = http_endpoints[i]
        logger.debug("Iterating methods for http endpoint '%s': %s", http_endpoint, methods_dict)
        i += 1

        http_methods: list[tuple[str, list[dict]]] = list(methods_dict.items())
        j: int = 0

        while not found and j < len(http_methods):

            method_tools: Optional[list[dict]] = None
            http_method, method_tools = http_methods[j]
            logger.debug("Iterating tools for http endpoint '%s (%s)': %s", http_endpoint, http_method, method_tools)
            j += 1

            k: int = 0
            while not found and k < len(method_tools):
                tool: dict = method_tools[k]
                logger.debug("Checking tool for http endpoint '%s (%s)': %s", http_endpoint, http_method, tool)
                k += 1

                if tool.get("function", {}).get("name") == tool_call_function_name:
                    found = True
                    logger.debug("Found http endpoint and method for tool call '%s': '%s' (%s)", tool_call_function_name, http_endpoint, http_method)
    if not found:
        logger.error("NOT found http endpoint or method for tool call: '%s'", tool_call_function_name)

    return http_endpoint, http_method
