"""
Author: Anton Pastoriza
"""

from dataclasses import dataclass
from typing import Optional

from model.protocol import Message


@dataclass
class Function:
    """
    A class representing a function that can be called by a tool.

    Attributes:
        name (str): The name of the function.
        arguments (str): The arguments to be passed to the function, represented as a string.
    """
    name: str
    arguments: str


@dataclass
class ToolCall:
    """
    A class representing a call to a tool, including the tool's type and the function to be executed.

    Attributes:
        id (str): A unique identifier for the tool call.
        type (str): The type of the tool (e.g., API, script).
        function (Function): The function to be called by the tool.
    """
    id: str
    type: str
    function: Function


@dataclass
class AssistantMessage(Message):
    """
    A class representing a message from an assistant, which may include tool calls.

    Attributes:
        content (str): The content of the message.
        role (str): The role of the sender (typically 'assistant').
        name (Optional[str]): The name of the assistant, if applicable.
        tool_calls (Optional[list[ToolCall]]): A list of ToolCall objects representing any tool calls associated with the message.
    """
    tool_calls: Optional[list[ToolCall]]

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "AssistantMessage":
        """
        Create an AssistantMessage object from a dictionary.

        Args:
            data (dict[str, any]): A dictionary containing assistant message data.

        Returns:
            AssistantMessage: An AssistantMessage object created from the provided dictionary.
        """
        return cls(
            content=data.get("content", ""),
            role=data.get("role", ""),
            name=data.get("name", None),
            tool_calls=data.get("tool_calls", None)
        )
