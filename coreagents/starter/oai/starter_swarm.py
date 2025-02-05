"""
Author: Anton Pastoriza
"""

import sys
import threading
from logging import Logger

from agent.oai.swarm_master import SwarmMaster
from config.oai import language_model
from model.vo import AgentVO
from starter.helper import sysargv_helper
from utils import logging_config, http_invoker_helper

logger: Logger = logging_config.get_logger(__name__)


def _main():
    # sys.argv[0] is the script name, so the first argument is at index 1
    if len(sys.argv) > 1:
        swarm_identifier: str = sysargv_helper.retrieve_parameter_as_str(1, "Swarm identifier")
        http_swarm_port: int = sysargv_helper.retrieve_parameter_as_int(2, "HTTP Swarm port", 10000)
        agent_registry_host: str = sysargv_helper.retrieve_parameter_as_str(3, "Agent registry", "http://registry-agent:7000")

        logger.info("Starting swarm: Identifier: '%s'", swarm_identifier)
        logger.info("Starting swarm: HTTP Service port: %d", http_swarm_port)
        logger.info("Starting swarm: Agent registry: '%s'", agent_registry_host)

        _start_swarm(swarm_identifier, http_swarm_port, agent_registry_host)

    else:
        logger.error("Error starting agent: No parameters passed.")
        sys.exit(1)  # Exit with a status code of 1 to indicate an error


def _start_swarm(swarm_identifier: str, http_port: int, agent_registry_host: str):
    endpoint: str = f"/swarms/{swarm_identifier}"
    swarm_vo_dict: dict = http_invoker_helper.get(agent_registry_host, endpoint)
    if not swarm_vo_dict:
        logger.error("Error starting swarm: Invalid registry descriptor for swarm '%s'", swarm_identifier)
    else:
        identifier: str = swarm_vo_dict["identifier"]
        swarm_type: str = swarm_vo_dict["swarm_type"]
        agent_vos: list[AgentVO] = _compose_agents_list(swarm_vo_dict)
        if identifier == swarm_identifier:
            logger.info("Starting swarm: Swarm type: '%s'", swarm_type)
            if not agent_vos:
                logger.error("Error starting swarm: Swarm '%s' has no linked agents", identifier)
                sys.exit(1)
            else:
                swarm: SwarmMaster = SwarmMaster(
                    name=identifier,
                    description=f"{identifier} of type {swarm_type}",
                    model_config=language_model.model_config(),
                    agent_vos=agent_vos,
                    http_port=http_port
                )
                threading.Thread(target=swarm.start).start()
        else:
            logger.error("Error starting swarm: Invalid registry descriptor. Expected '%s' but found '%s'", swarm_identifier, identifier)
            sys.exit(1)


def _compose_agents_list(swarm_vo_dict: dict) -> list[AgentVO]:
    agent_vos: list[AgentVO] = []
    dict_of_agent_vos: list[dict] = swarm_vo_dict["agents"]
    for dict_of_agent_vo in dict_of_agent_vos:
        agent_vo = AgentVO.from_dict(dict_of_agent_vo)
        agent_vos.append(agent_vo)
    return agent_vos


if __name__ == "__main__":
    _main()
