"""
Author: Anton Pastoriza
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    """
    A class representing a message in a Chat Completion conversation.

    Each message object has content and a role (either system, user, or assistant).
    - The system message is optional and can be used to set the behavior of the assistant.
    - The user messages provide requests or comments for the assistant to respond to
    - Assistant messages store previous assistant responses, but can also be written to give examples of desired behavior

    Attributes:
        content (str): The content of the message.
        role (str): The role of the sender (either system, user, or assistant).
        name (Optional[str]): The name of the sender, if applicable.
        pending_user_reply: The flag that reflex if the swarm expects an user response
    """
    content: str
    role: str
    name: Optional[str]
    pending_user_reply: bool
    datetime_value: str

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "Message":
        """
        Create a Message object from a dictionary.

        Args:
            data (dict[str, any]): A dictionary containing message data.

        Returns:
            Message: A Message object created from the dictionary.
        """
        return cls(
            content=data.get("content", ""),
            role=data.get("role", ""),
            name=data.get("name", None),
            pending_user_reply=data.get("pending_user_reply", None),
            datetime_value=data.get("datetime_value",datetime.now().timestamp()
)
        )

    def to_dict(self):
        """
        Convert the Message object to a dictionary.

        Returns:
            dict[str, any]: A dictionary representation of the Message object.
        """
        return {
            "content": self.content,
            "role": self.role,
            "name": self.name,
            "pending_user_reply": self.pending_user_reply,
            "datetime_value": self.datetime_value
        }


@dataclass
class Header:
    """
    A class representing the header information of a conversation.

    Attributes:
        user_id (str): The ID of the user involved in the conversation.
        conversation_id (str): The ID of the conversation.
        sender (str): The sender of the message (e.g., the agent identifier, the swarm identifier, etc.).
    """
    user_id: str
    conversation_id: str
    sender: str

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "Header":
        """
        Create a Header object from a dictionary.

        Args:
            data (dict[str, any]): A dictionary containing header data.

        Returns:
            Header: A Header object created from the dictionary.
        """
        return cls(
            user_id=data.get("user_id", ""),
            conversation_id=data.get("conversation_id", ""),
            sender=data.get("sender", "")
        )

    def to_dict(self):
        """
        Convert the Header object to a dictionary.

        Returns:
            dict[str, any]: A dictionary representation of the Header object.
        """
        return {
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "sender": self.sender
        }


@dataclass
class InitialMessage:
    """
    A class representing the initial message of a conversation.

    Attributes:
        swarm (str): The ID of the swarm framing the conversation.
        user (str): The ID of the user initiating the conversation.
        request (str): The initial request or message content from the user.
    """
    swarm: str
    user: str
    request: str

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "InitialMessage":
        """
        Create an InitialMessage object from a dictionary.

        Args:
            data (dict[str, any]): A dictionary containing initial message data.

        Returns:
            InitialMessage: An InitialMessage object created from the dictionary.
        """
        return cls(
            swarm=data.get("swarm", ""),
            user=data.get("user", ""),
            request=data.get("request", "")
        )

    def to_dict(self):
        """
        Convert the InitialMessage object to a dictionary.

        Returns:
            dict[str, any]: A dictionary representation of the InitialMessage object.
        """
        return {
            "swarm": self.swarm,
            "user": self.user,
            "request": self.request
        }


@dataclass
class ReplyMessage:
    """
    A class representing the initial message of a conversation.

    Attributes:
        conversation_id (str): The ID of the conversation.
        user_id (str): The ID of the user initiating the conversation.
        content (str): The reply message content from the user.
    """
    conversation_id: str
    user_id: str
    content: str

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "ReplyMessage":
        """
        Create an ReplyMessage object from a dictionary.

        Args:
            data (dict[str, any]): A dictionary containing initial message data.

        Returns:
            ReplyMessage: An InitialMessage object created from the dictionary.
        """
        return cls(
            conversation_id=data.get("conversation_id", ""),
            user_id=data.get("user_id", ""),
            content=data.get("content", "")
        )

    def to_dict(self):
        """
        Convert the ReplyMessage object to a dictionary.

        Returns:
            dict[str, any]: A dictionary representation of the InitialMessage object.
        """
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "content": self.content
        }


@dataclass
class Conversation:
    """
    A class representing a conversation, which consists of a header and a list of messages.

    Attributes:
        header (Header): The header information of the conversation.
        messages (list[Message]): A list of Message objects that make up the conversation.
    """
    header: Header
    messages: list[Message]
