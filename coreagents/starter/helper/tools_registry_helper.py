from logging import Logger
from typing import Optional

from starter.helper.oai import oai_tools_helper
from utils import logging_config, http_invoker_helper

logger: Logger = logging_config.get_logger(__name__)


def get_tools_from_registry(tool_registry_host: str, tools_identifier: list[str]) -> Optional[dict[str, dict[str, list[dict]]]]:
    agent_tools: Optional[dict[str, dict[str, list[dict]]]] = None

    for tool_identifier in tools_identifier:
        endpoint: str = f"/tools/{tool_identifier}"
        tool_vo_dict: dict = http_invoker_helper.get(tool_registry_host, endpoint)
        if tool_vo_dict is None:
            logger.debug("No tools found for '%s' at '%s'", tool_identifier, tool_registry_host)
        else:
            swagger_url: str = tool_vo_dict.get("swagger")
            if not swagger_url:
                logger.error("Missing swagger URL for tool '%s'. Got dict: %s", tool_identifier, tool_vo_dict)
            else:
                if agent_tools is None:
                    agent_tools = {}

                last_slash_index: int = swagger_url.rfind("/")
                root_swagger_url: str = swagger_url[:last_slash_index]

                tools_functions: dict[str, dict[str, list[dict]]] = oai_tools_helper.generate_tool_functions(swagger_url)
                for path, functions in tools_functions.items():
                    full_path: str = root_swagger_url + path
                    agent_tools[full_path] = functions

    return agent_tools
