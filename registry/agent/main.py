"""
Author: Anton Pastoriza
"""
import os
import threading
import yaml
from typing import Optional
from logging import Logger

import uvicorn
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse

from factory import web_factory
from model.vo import AgentVO, SwarmVO
from utils import logging_config

app: FastAPI = web_factory.create_app()

logger: Logger = logging_config.get_logger(__name__)


@app.get("/agents")
def agents() -> list[AgentVO]:
    """
    Fetch a list of all agents by reading and parsing YAML files.

    Returns:
        list[AgentVO]: A list of AgentVO objects representing the agents.
    """
    agents_list: list[AgentVO] = []
    yaml_files: list[Path] = _list_yaml_files()
    # Iterate over each YAML file
    for yaml_file in yaml_files:
        try:
            with yaml_file.open("r") as file:
                content = file.read()
                data_dict = yaml.safe_load(content)
                if "agent_type" in data_dict:
                    agent_vo = AgentVO.from_dict(data_dict)
                    agents_list.append(agent_vo)
        except yaml.YAMLError as e:
            logger.error("Error parsing YAML file '%s': %s", yaml_file, e)
        except Exception as e:
            logger.error("Unexpected error while processing file '%s': %s", yaml_file, e)
    return agents_list


@app.get("/agents/{identifier}")
def agent(identifier: str) -> Optional[AgentVO]:
    """
    Fetch a single agent by its identifier.

    Args:
        identifier (str): The identifier of the agent to retrieve.

    Returns:
        Optional[AgentVO]: The AgentVO object if found, otherwise None.

    Raises:
        HTTPException: If the agent is not found, a 404 error is raised.
    """
    agent_vo: Optional[AgentVO] = None
    yaml_files: list[Path] = _list_yaml_files()
    i: int = 0
    agent_found: bool = False
    # Iterate over each YAML file until agent YAML is not found
    while i < len(yaml_files) and not agent_found:
        try:
            with yaml_files[i].open("r") as file:
                content = file.read()
                data_dict = yaml.safe_load(content)
                if "agent_type" in data_dict:
                    if data_dict["identifier"] == identifier:
                        agent_vo = AgentVO.from_dict(data_dict)
                        agent_found = True
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {yaml_files[i]}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while processing file {yaml_files[i]}: {e}")
        i += 1
    if not agent_found:
        # If the agent is not found, raise a 404 error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with identifier '{identifier}' not found"
        )
    return agent_vo


@app.get("/agents/avatar/{identifier}",
         responses={
             200: {
                 "content": {
                     "image/png": {}
                 }
             }
         })
def avatar(identifier: str) -> FileResponse:
    """
    Fetch a single avatar by its agent identifier.

    :param identifier: The identifier of the agent to retrieve its avatar.
    :return: The avatar file
    """
    avatar_path: str = f"{identifier}.png"
    if not os.path.exists(avatar_path):
        # If the file is not found, use default
        logger.error(f"Avatar file '{avatar_path}' does not exist. Using default avatar.")
        avatar_path = "default.png"

    avatar_response: FileResponse = FileResponse(
        avatar_path,
        media_type="image/png"
    )
    return avatar_response


@app.get("/swarms")
def swarms() -> list[SwarmVO]:
    """
    Fetch a list of all swarms by reading and parsing YAML files.

    Returns:
        list[SwarmVO]: A list of SwarmVO objects representing the swarms.
    """
    swarms_list: list[SwarmVO] = []
    yaml_files: list[Path] = _list_yaml_files()
    # Iterate over each YAML file
    for yaml_file in yaml_files:
        try:
            with yaml_file.open("r") as file:
                content = file.read()
                data_dict = yaml.safe_load(content)
                if "swarm_type" in data_dict:
                    swarm_vo = _compose_swarm_vo(data_dict)
                    swarms_list.append(swarm_vo)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {yaml_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while processing file {yaml_file}: {e}")
    return swarms_list


@app.get("/swarms/{identifier}")
def swarm(identifier: str) -> SwarmVO:
    """
    Fetch a single swarm by its identifier.

    Args:
        identifier (str): The identifier of the swarm to retrieve.

    Returns:
        SwarmVO: The SwarmVO object if found.

    Raises:
        HTTPException: If the swarm is not found, a 404 error is raised.
        HTTPException: If the swarm structure is invalid, a 422 error is raised.
    """
    swarm_vo: Optional[SwarmVO] = None
    yaml_files: list[Path] = _list_yaml_files()
    # Iterate over each YAML file
    i: int = 0
    swarm_found: bool = False
    while i < len(yaml_files) and not swarm_found:
        try:
            with yaml_files[i].open("r") as file:
                content = file.read()
                data_dict = yaml.safe_load(content)
                if "swarm_type" in data_dict:
                    if data_dict["identifier"] == identifier:
                        swarm_vo = _compose_swarm_vo(data_dict)
                        if not _is_valid_swarm_vo_structure(swarm_vo):
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Invalid swarm structure for '{identifier}'. Check system logs for details."
                            )
                        swarm_found = True
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {yaml_files[i]}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while processing file {yaml_files[i]}: {e}")
        i += 1

    if not swarm_found:
        # If the swarm is not found, raise a 404 error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Swarm with identifier '{identifier}' not found"
        )
    return swarm_vo


@app.get("/health")
def health() -> dict:
    """
    Check the health of the service.

    Returns:
        dict: A dictionary containing the registry name and the current thread name.
    """
    return {
        "registry": "agent-registry",
        "thread": f"{threading.current_thread().name}"
    }


def _compose_swarm_vo(swarm_vo_dict: dict) -> SwarmVO:
    """
    Compose a SwarmVO object from a dictionary of swarm data.

    Args:
        swarm_vo_dict (dict): A dictionary containing swarm data.

    Returns:
        SwarmVO: The composed SwarmVO object.
    """
    swarm_vo = SwarmVO(
        identifier=swarm_vo_dict["identifier"],
        swarm_type=swarm_vo_dict["swarm_type"],
        agents=[]
    )
    for agent_identifier in swarm_vo_dict["agents"]:
        agent_vo: AgentVO = agent(agent_identifier)
        swarm_vo.agents.append(agent_vo)

    return swarm_vo


def _is_valid_swarm_vo_structure(swarm_vo: SwarmVO) -> bool:
    """
    Validate the structure of a SwarmVO object based on its agents' RACI roles.

    Args:
        swarm_vo (SwarmVO): The SwarmVO object to validate.

    Returns:
        bool: True if the structure is valid, False otherwise.

    Logs errors if the structure is invalid based on the following conditions:
        - No responsible agents found
        - No accountable agents found
        - More than one accountable agent found
        - More than one responsible agent found
    """
    valid: bool = True
    total_accountable: int = 0
    total_responsible: int = 0

    for agent_vo in swarm_vo.agents:
        if agent_vo.raci_role.lower() == "r":
            total_responsible += 1
        elif agent_vo.raci_role.lower() == "a":
            total_accountable += 1

    if total_responsible == 0:
        logger.error(f"No responsible agents found for {swarm_vo.identifier}")
        valid = False
    elif total_accountable == 0:
        logger.error(f"No accountable agents found for {swarm_vo.identifier}")
        valid = False
    elif total_accountable > 1:
        logger.error(f"More than one accountable agents found for {swarm_vo.identifier}. Found: {total_accountable}")
        valid = False
    elif total_responsible > 1:
        logger.error(f"More than one responsible agents found for {swarm_vo.identifier}. Found: {total_responsible}")
        valid = False
    else:
        logger.debug(f"Valid structure for {swarm_vo.identifier}")

    return valid


def _list_yaml_files() -> list[Path]:
    """
    List all YAML files in the current directory and its subdirectories.

    Returns:
        list[Path]: A list of Path objects pointing to YAML files.
    """
    # Specify the directory
    directory = Path("./")

    # Recursively list all YAML files
    yaml_files = directory.rglob('*.yaml')
    yaml_files = list(yaml_files) + list(directory.rglob('*.yml'))
    return yaml_files


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7000)
