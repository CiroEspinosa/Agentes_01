"""
Author: Anton Pastoriza
"""

from model.protocol import Conversation, Header, Message


def to_dict_conversation(conversation: Conversation) -> dict:
    """
    Convert a Conversation object to a dictionary.

    Args:
        conversation (Conversation): The Conversation object to convert.

    Returns:
        dict: A dictionary representation of the Conversation, including its header and messages.
    """
    header_dict = conversation.header.to_dict()
    messages_dict: list[dict] = []
    if conversation.messages is not None:
        messages_dict = to_dict_messages(conversation.messages)

    conversation_dict: dict = {
        "header": header_dict,
        "messages": messages_dict
    }
    return conversation_dict


def to_conversation_from_dict(conversation_dict: dict) -> Conversation:
    """
    Convert a dictionary to a Conversation object.

    Args:
        conversation_dict (dict): A dictionary containing conversation data with keys "header" and "messages".

    Returns:
        Conversation: A Conversation object created from the provided dictionary.
    """
    header_dict: dict = conversation_dict["header"]
    messages_dict: list[dict] = conversation_dict["messages"]

    header: Header = Header.from_dict(header_dict)
    messages: list[Message] = to_messages_from_dict(messages_dict)

    conversation: Conversation = Conversation(
        header=header,
        messages=messages
    )
    return conversation


def to_dict_messages(messages: list[Message]) -> list[dict]:
    """
    Convert a list of Message objects to a list of dictionaries.

    Args:
        messages (list[Message]): A list of Message objects to convert.

    Returns:
        list[dict]: A list of dictionaries representing the messages.
    """
    messages_dict: list[dict] = []
    for message in messages:
        messages_dict.append(message.to_dict())

    return messages_dict


def to_messages_from_dict(messages_dict: list[dict]) -> list[Message]:
    """
    Convert a list of dictionaries to a list of Message objects.

    Args:
        messages_dict (list[dict]): A list of dictionaries representing messages.

    Returns:
        list[Message]: A list of Message objects created from the provided dictionaries.
    """
    messages: list[Message] = []
    for message_dict in messages_dict:
        messages.append(Message.from_dict(message_dict))

    return messages
