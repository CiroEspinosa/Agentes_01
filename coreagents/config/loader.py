"""
Author: Anton Pastoriza
"""

import json
from logging import Logger

from model.vo import AgentVO
from typing import Optional

from utils import logging_config

logger: Logger = logging_config.get_logger(__name__)


def load_agents(json_file_path: str) -> list[AgentVO]:
    # Read and parse the JSON file
    array_of_agent_vos: list[AgentVO] = []
    dict_of_agent_vos: list[dict] = _load_file_of_agent_vos(json_file_path)

    total_accountable: int = 0
    total_responsible: int = 0
    if not dict_of_agent_vos:
        logger.error(f"File {json_file_path} is empty")
    else:
        for dict_of_agent_vo in dict_of_agent_vos:
            agent_vo = AgentVO.from_dict(dict_of_agent_vo)
            array_of_agent_vos.append(agent_vo)
            if agent_vo.raci_role.lower() == "r":
                total_responsible += 1
            elif agent_vo.raci_role.lower() == "a":
                total_accountable += 1

    if total_responsible == 0:
        logger.error(f"No responsible agents found for {json_file_path}")
    elif total_accountable == 0:
        logger.error(f"No accountable agents found for {json_file_path}")
    elif total_accountable > 1:
        logger.error(f"More than one accountable agents found for {json_file_path}. Found: {total_accountable}")
    elif total_responsible > 1:
        logger.error(f"More than one responsible agents found for {json_file_path}. Found: {total_responsible}")

    return array_of_agent_vos


def load_agent(identifier: str, json_file_path: str) -> Optional[AgentVO]:
    agent_vo: Optional[AgentVO] = None

    dict_of_agent_vos: list[dict] = _load_file_of_agent_vos(json_file_path)
    if not dict_of_agent_vos:
        logger.error(f"File {json_file_path} is empty")
    else:
        agent_vo_found: bool = False
        i: int = 0

        while i < len(dict_of_agent_vos) and not agent_vo_found:
            dict_of_agent_vo = dict_of_agent_vos[i]
            if dict_of_agent_vo["identifier"] == identifier:
                agent_vo = AgentVO.from_dict(dict_of_agent_vo)
                agent_vo_found = True
            else:
                i += 1

        if not agent_vo_found:
            logger.error(f"Agent {identifier} not found in file {json_file_path} is empty")

    return agent_vo


def _load_file_of_agent_vos(json_file_path: str) -> list[dict]:
    dict_of_agent_vos: list[dict] = []
    with open(json_file_path, "r") as file:
        dict_of_agent_vos = json.load(file)
        # self.logger.debug(f"{dict_of_agent_vos}")

    return dict_of_agent_vos
