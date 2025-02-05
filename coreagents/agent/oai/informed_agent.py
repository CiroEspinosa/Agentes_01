"""
This module defines the `InformedAgent` class, which is a specialized agent
inheriting from the `OpenAIRaciAgent` class. This agent represents an 'Informed' role in a RACI model.

Author: Anton Pastoriza
"""

from agent.oai.oai_raci_agent import OpenAIRaciAgent


class InformedAgent(OpenAIRaciAgent):
    """
    A specialized agent that represents the 'Informed' role in the RACI model.

    Inherits from:
        OpenAIRaciAgent: The base class for agents operating within the OpenAI RACI framework.
    """
    pass
