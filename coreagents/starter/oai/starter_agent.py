"""
Author: Anton Pastoriza
"""

import sys
import threading
from logging import Logger
from typing import Optional

from agent.oai.consulted_agent import ConsultedAgent
from agent.oai.oai_raci_agent import OpenAIRaciAgent
from agent.oai.user_proxy_agent import UserProxyAgent
from config.oai import language_model
from model.vo import AgentVO
from starter.helper import sysargv_helper, tools_registry_helper
from utils import logging_config, http_invoker_helper

from agent.oai.git_specialist_agent import GitSpecialistAgent
logger: Logger = logging_config.get_logger(__name__)


def _start_agent(agent_identifier: str, http_port: int, agent_registry_host: str, tool_registry_host: str):
    endpoint: str = f"/agents/{agent_identifier}"
    agent_vo_dict: dict = http_invoker_helper.get(agent_registry_host, endpoint)
    if not agent_vo_dict:
        logger.error("Error starting agent: Invalid registry descriptor for agent '%s'", agent_identifier)
    else:
        agent_vo: AgentVO = AgentVO.from_dict(agent_vo_dict)
        if agent_vo.identifier == agent_identifier:
            agent: Optional[OpenAIRaciAgent] = None
            agent_tools: Optional[dict[str, dict[str, list[dict]]]] = None
            logger.info("Starting agent: Agent model %s", agent_vo.model)
            logger.info("Starting agent: Agent randomness %d", agent_vo.randomness)
            logger.info("Starting agent: Agent has no linked tools")
            if not agent_vo.tools:
                logger.info("Starting agent: Agent has no linked tools")
            else:
                logger.info("Starting agent: Agent has linked tools: %s", agent_vo.tools)
                agent_tools = tools_registry_helper.get_tools_from_registry(tool_registry_host, agent_vo.tools)

            if not agent_vo.rag_enabled:
                logger.info("Starting agent: Agent has RAG disabled")
            else:
                logger.info("Starting agent: Agent has RAG enabled")

            logger.info("Starting agent: agent type: '%s'", agent_vo.agent_type)
            if agent_vo.agent_type == "user_proxy":
                agent = UserProxyAgent(
                    name=agent_vo.identifier,
                    description=f"{agent_vo.agent_description}. {agent_vo.goals}",
                    model_config=language_model.model_config(
                        randomness=agent_vo.randomness,
                        model=agent_vo.model
                    ),
                    http_port=http_port,
                    tools=agent_tools,
                    rag_enabled=agent_vo.rag_enabled
                )
            elif agent_vo.agent_type == "assistant":
                agent = ConsultedAgent(
                    name=agent_vo.identifier,
                    description=f"{agent_vo.agent_description}. {agent_vo.goals}",
                    model_config=language_model.model_config(
                        randomness=agent_vo.randomness,
                        model=agent_vo.model
                    ),
                    http_port=http_port,
                    tools=agent_tools,
                    rag_enabled=agent_vo.rag_enabled
                )
            elif agent_vo.agent_type == "git-specialist":
                agent = GitSpecialistAgent(
                    name=agent_vo.identifier,
                    description=f"{agent_vo.agent_description}. {agent_vo.goals}",
                    model_config=language_model.model_config(
                        randomness=agent_vo.randomness,
                        model=agent_vo.model
                    ),
                    http_port=http_port,
                    tools=agent_tools,
                    rag_enabled=agent_vo.rag_enabled
                )
            if agent is None:
                logger.error("Error starting agent: Unknown agent '%s' of type '%s'", agent_vo.identifier, agent_vo.agent_type)
                sys.exit(1)
            else:
                threading.Thread(target=agent.start).start()
        else:
            logger.error("Error starting agent: Invalid registry descriptor. Expected '%s' but found '%s'", agent_identifier, agent_vo.identifier)
            sys.exit(1)


def _main():
    if len(sys.argv) > 1:
        # sys.argv[0] is the script name, so the first argument is at index 1
        agent_identifier: str = sysargv_helper.retrieve_parameter_as_str(1, "Agent identifier")
        http_service_port: int = sysargv_helper.retrieve_parameter_as_int(2, "HTTP Service port", 10000)
        agent_registry_host: str = sysargv_helper.retrieve_parameter_as_str(3, "Agent registry", "http://registry-agent:7000")
        tool_registry_host: str = sysargv_helper.retrieve_parameter_as_str(4, "Tool registry", "http://registry-tool:7001")

        logger.info("Starting agent: Identifier: '%s'", agent_identifier)
        logger.info("Starting agent: HTTP Service port: %d", http_service_port)
        logger.info("Starting agent: Agent registry: '%s'", agent_registry_host)

        _start_agent(agent_identifier, http_service_port, agent_registry_host, tool_registry_host)

    else:
        logger.error("Error starting agent: No parameters passed.")
        sys.exit(1)  # Exit with a status code of 1 to indicate an error


if __name__ == "__main__":
    _main()
