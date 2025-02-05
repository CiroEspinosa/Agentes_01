"""
This module provides functions to handle the identification of a single-role agent,
and to compose system messages and next agent message content in a role-play game context.

Author: Anton Pastoriza
"""
from datetime import datetime
from logging import Logger
from typing import Optional

from model.protocol import Message
from model.vo import AgentVO
from utils import logging_config

logger: Logger = logging_config.get_logger(__name__)


def identify_single_role_agent(agent_vos: list[AgentVO], raci_role: str) -> Optional[AgentVO]:
    """
    Identifies a single agent with a specific RACI role from a list of agents.

    Args:
        agent_vos (list[AgentVO]): A list of AgentVO objects representing the agents.
        raci_role (str): The RACI role to identify (e.g., 'accountable', 'responsible').

    Returns:
        Optional[AgentVO]: The AgentVO object corresponding to the identified agent, or None if no such agent is found.

    Raises:
        ValueError: If no agent or more than one agent with the specified role is found.
    """
    total_agents: int = 0
    found_agent_vo: Optional[AgentVO] = None
    for agent_vo in agent_vos:
        if agent_vo.raci_role.lower() == raci_role:
            found_agent_vo = agent_vo
            total_agents += 1
    if total_agents == 0:
        raise ValueError(f"No accountable agents found at {agent_vos}")
    elif total_agents > 1:
        raise ValueError(f"More than one accountable agents found at {agent_vos}. Found: {total_agents}")
    return found_agent_vo


def compose_initial_system_message(swarm_name: str, agent_vos: list[AgentVO]) -> Message:
    """
    Composes the initial system message for the role-play game.

    Args:
        swarm_name (str): The name of the swarm (or system) sending the message.
        agent_vos (list[AgentVO]): A list of AgentVO objects representing the agents and their roles.

    Returns:
        Message: A Message object containing the initial system message.
    """
    content: str = "You are in a role play game. The following roles are available:\n"
    for agent_vo in agent_vos:
        content += f" - {agent_vo.identifier}: "
        if agent_vo.agent_description:
            content += f" - {agent_vo.agent_description}"
            if agent_vo.agent_description.endswith("."):
                content += " "
            else:
                content += ". "
        if agent_vo.goals:
            content += f" - {agent_vo.goals}"
            if agent_vo.goals.endswith("."):
                content += "\n"
            else:
                content += ".\n"

    system_message = Message(
        content=content,
        role="system",
        name=swarm_name,
        pending_user_reply=False,
        datetime_value=datetime.now().timestamp()
    )

    logger.info("Initialized swarm with %d agent(s)", len(agent_vos))
    logger.debug("Initialization message: %s", content)
    return system_message


def compose_next_agent_message_content(agent_vos: list[AgentVO], previous_agent: str) -> str:
    """
    Composes the content of the next agent message, excluding the previous agent from selection.

    Args:
        agent_vos (list[AgentVO]): A list of AgentVO objects representing the agents and their roles.
        previous_agent (str): The identifier of the agent that made the previous message.

    Returns:
        str: A string containing the prompt for the next agent's message selection.
    """
    first_agent: bool = True
    content: str = "Read the above conversation. Then select the next role to play from the following list: "
    for agent_vo in agent_vos:
        agent_identifier: str = agent_vo.identifier
        # agent cannot reply two consecutive times
        if not agent_identifier == previous_agent:
            if first_agent:
                content += f"{agent_vo.identifier}"
                first_agent = False
            else:
                content += f", {agent_vo.identifier}"
    content += ". Respond with ONLY the name of the role and DO NOT provide a reason."
    return content
