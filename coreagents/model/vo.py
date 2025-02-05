"""
Author: Anton Pastoriza, Jose Luis Martin
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AgentVO:
    """
    A class representing an agent in the system.

    Attributes:
        identifier (str): A unique identifier for the agent.
        raci_role (str): The RACI role assigned to the agent (e.g., Responsible, Accountable).
        agent_type (str): The type of the agent (e.g., AI, human, system).
        agent_description (str): A brief description of the agent's purpose or function.
        goals (str): The goals or objectives assigned to the agent.
        tools (list[str]): List of unique tools identifiers assigned to the agent.
    """
    identifier: str
    raci_role: str
    agent_type: str
    agent_description: str
    goals: str
    tools: list[str]
    rag_enabled: bool
    model: str
    randomness: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentVO":
        """
        Create an AgentVO object from a dictionary.

        Args:
            data (Dict[str, Any]): A dictionary containing agent data.

        Returns:
            AgentVO: An AgentVO object created from the provided dictionary.
        """
        return cls(
            identifier=data.get("identifier", ""),
            raci_role=data.get("raci_role", ""),
            agent_type=data.get("agent_type", ""),
            agent_description=data.get("agent_description", ""),
            goals=data.get("goals", ""),
            tools=data.get("tools", []),
            rag_enabled=data.get("rag_enabled", False),
            model=data.get("model", "gpt-4o"),
            randomness=data.get("randomness", 0.0)
        )


@dataclass
class SwarmVO:
    """
    A class representing a swarm, which is a collection of agents working together.

    Attributes:
        identifier (str): A unique identifier for the swarm.
        swarm_type (str): The type of the swarm (e.g., task force, team).
        agents (list[AgentVO]): A list of AgentVO objects representing the agents in the swarm.
    """
    identifier: str
    swarm_type: str
    agents: list[AgentVO]


@dataclass
class ToolVO:
    id: str
    description: str
    keywords: str
    swagger: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolVO":
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            keywords=data.get("keywords", ""),
            swagger=data.get("swagger", "")
        )
