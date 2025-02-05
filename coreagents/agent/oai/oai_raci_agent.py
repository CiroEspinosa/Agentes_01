"""
Author: Anton Pastoriza
"""

import json
import os
import threading
import time
from datetime import datetime
from logging import Logger
from typing import Optional, override

from config.llm import ModelConfig
from embeddings.milvusdb import MilvusClient
from embeddings.pineconedb import PineconeClient
from model.protocol import Conversation, Message
from openai import (
    APIConnectionError,
    APIError,
    APIResponseValidationError,
    AzureOpenAI,
    InternalServerError,
    OpenAIError,
    PermissionDeniedError,
)
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from utils import logging_config

from agent.helper.oai import agent_tools_helper
from agent.raci_agent import RaciAgent


class OpenAIRaciAgent(RaciAgent):
    """
    A specialized RaciAgent that integrates with OpeAzureOpenAI's API to process conversations
    and generate responses using AI models.

    Attributes:
        model_config (ModelConfig): Configuration for the OpenAI model, including API key and model name.
        client (AzureOpenAI): The AzureOpenAI client instance for interacting with the AzureOpenAI API.
    """

    def __init__(
        self,
        name: str,
        description: str,
        model_config: ModelConfig,
        http_port: int = 9000,
        tools: Optional[dict[str, dict[str, list[dict]]]] = None,
        rag_enabled: bool = False,
    ):
        """
        Initialize an OpenAIRaciAgent instance with the provided parameters.

        Args:
            name (str): The name of the agent.
            description (str): A brief description of the agent.
            model_config (ModelConfig): The configuration object for the AzureOpenAI model.
            http_port (int): The port number for the HTTP server. Defaults to 9000.
            tools Optional[dict[str, dict[str, list[dict]]]]: List of unique tools assigned to the agent. Defaults to None.
            rag_enabled (bool): Whether the RAG is enabled in the agent. Defaults to False.
        """
        super().__init__(name, description, http_port)
        self.model_config = model_config
        self.client = AzureOpenAI(
            api_key=model_config.api_key,
            api_version=model_config.api_version,
            azure_endpoint=model_config.base_url,
        )
        self.tools = tools
        self.rag_enabled = rag_enabled
        self.pinecone_handler: Optional[PineconeHandler] = None
        if self.rag_enabled:
            self.pinecone_handler = PineconeHandler(self)

    @override
    def process_response(self, conversation: Conversation):
        """
        Process a conversation by generating a response using the AzureOpenAI API.

        This method overrides the base class's process_response method to include
        AI-driven response generation.

        Args:
            conversation (Conversation): The conversation object to process.
        """
        agent_requestor: str = conversation.header.sender
        self.logger.debug("Processing %s from %s", conversation, agent_requestor)

        if self.rag_enabled:
            self.pinecone_handler.messages = conversation.messages

        response: str = self._complete(conversation.messages)

        self.logger.debug(
            "From: '%s' to: '%s' \n response: %s", self.name, agent_requestor, response
        )

        conversation.messages.append(
            Message(
                content=response,
                role="assistant",
                name=self.name,
                pending_user_reply=False,
                datetime_value=datetime.now().timestamp(),
            )
        )

        conversation.header.sender = self.name

        self.send_message(agent_requestor, conversation)

    @override
    async def chat(self, request: dict) -> dict:
        """
        Handles a single chat interaction for the assistant, taking a user request,
        processing it to generate a response, and returning the response in the appropriate format.

        Args:
            request (dict): A dictionary containing the request details, expected to have
                            keys that map to `Message` attributes such as 'content', 'role',
                            and 'name'. This represents the user input message.

        Returns:
            dict: A dictionary representing the response from the assistant, containing keys like
                  'content' (the assistant reply), 'role' (set to 'assistant'), and 'name'
                  (set to the assistant name).

        Behavior:
            - Converts the input request dictionary into a `Message` object.
            - Sets the role of the message to "system" if it is not specified.
            - Retrieves any previous messages to provide context, then creates a list of messages
              including the current one.
            - Calls the `_complete()` method with the list of messages to generate a response.
            - Returns the generated response in dictionary format, with the role set to "assistant".

        Example:
            request = {
                "content": "Hello, what can you tell me about the weather today?",
                "role": "user",
                "name": "User1"
            }
            response = await self.chat(request)
            # response would look like:
            # {
            #     "content": "The weather today is sunny with a high of 25°C.",
            #     "role": "assistant",
            #     "name": "AssistantName"
            # }

        Note:
            The `_complete()` method should be defined to process the list of `Message` objects
            and generate an appropriate response based on the conversation history.
        """
        self.logger.info("Single chat of '%s'", self.name)
        message: Message = Message.from_dict(request)
        if not message.role:
            message.role = "system"

        messages: list[Message] = [message]

        if self.rag_enabled:
            self.pinecone_handler.messages = messages

        response: str = self._complete(messages)

        return Message(
            content=response,
            role="assistant",
            name=self.name,
            pending_user_reply=True,
            datetime_value=datetime.now().timestamp(),
        ).to_dict()

    @override
    async def health(self) -> dict:
        """
        Health check endpoint for the web server.

        Returns:
            dict: A dictionary containing the agent's name and current thread information.
        """
        self.logger.info("Checked status of '%s'", self.name)
        return {
            "agent": self.name,
            "model": self.model_config.model,
            "randomness": self.model_config.randomness,
            "tools": self.tools,
            "rag_enabled": self.rag_enabled,
            "thread": f"{threading.current_thread().name}",
        }

    def _complete(self, messages: list[Message]) -> str:
        """
        Generate a completion for the given messages using the AzureOpenAI API.

        Args:
            messages (list[Message]): A list of Message objects that make up the conversation.

        Returns:
            str: The content of the generated AI response.
        """
        oai_messages: list[dict] = self.fill_chat_completion_message_params(messages)
        content: str = ""

        if self.tools is None:
            response: ChatCompletion = self._do_completion_call(oai_messages)
            content = response.choices[0].message.content
        else:
            agent_tools: list[dict] = agent_tools_helper.compose_tools(self.tools)
            response: ChatCompletion = self._do_completion_call(
                oai_messages, agent_tools
            )
            response_message: ChatCompletionMessage = response.choices[0].message

            self.logger.debug(
                "Tools completion generated responded: %s", response_message
            )

            oai_messages.append(dict(response_message))

            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    tool_response: dict = agent_tools_helper.execute_call_from_tools(
                        self.tools, tool_call
                    )
                    oai_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": json.dumps(tool_response),
                        }
                    )

                response: ChatCompletion = self._do_completion_call(oai_messages)
                content = response.choices[0].message.content
            else:
                content = response_message.content
        return content

    def _do_completion_call(
        self,
        oai_messages: list[dict],
        agent_tools: Optional[list[dict]] = None,
        max_retries: int = 5,
        base_wait_time: int = 5,
    ) -> Optional[ChatCompletion]:
        """
        Perform a chat completion call to the AzureOpenAI API with optional tool support and retry logic.

        Args:
            oai_messages (list[dict]): A list of message dictionaries to send to the API.
            agent_tools (Optional[list[dict]], optional): A list of agent tools for tool-assisted completions.
                If provided, tool-related parameters are included in the API call. Defaults to None.
            max_retries (int, optional): The maximum number of retry attempts in case of specific API errors. Defaults to 5.
            base_wait_time (int, optional): The base wait time in seconds between retries, multiplied by the retry count. Defaults to 5.

        Returns:
            Optional[ChatCompletion]: The response from the AzureOpenAI API, or None if the call fails after all retries.
        """
        response: Optional[ChatCompletion] = None

        tool_completion: bool = agent_tools is not None
        system_assistant_message: dict[str, str] = (
            self._generate_system_assistant_message(tool_completion)
        )
        oai_messages.append(system_assistant_message)

        retries: int = 0

        while retries < max_retries and response is None:
            try:
                create_params = {
                    "model": self.model_config.model,
                    "messages": oai_messages,
                    "temperature": self.model_config.randomness,
                    "stream": False,
                    "max_tokens": self.model_config.max_tokens,
                }
                if tool_completion:
                    create_params.update({"tools": agent_tools, "tool_choice": "auto"})

                response = self.client.chat.completions.create(**create_params)
            except (
                APIConnectionError,
                InternalServerError,
                APIResponseValidationError,
            ) as e:
                self.logger.error(f"EXCEPTION: {e}")
                retries += 1
                wait_time = base_wait_time * retries
                self.logger.error(
                    "Error %s encountered.\nMessages: %s.\nRetrying %s/%s after %s seconds...",
                    e,
                    oai_messages,
                    retries,
                    max_retries,
                    wait_time,
                )
                time.sleep(wait_time)
            except (APIError, OpenAIError, PermissionDeniedError) as e:
                retries = max_retries
                self.logger.error("Error encountered: %s", e)
        return response

    def _generate_system_assistant_message(
        self, tool_completion: bool = False
    ) -> dict[str, str]:
        """
        Generate a system assistant message to be appended to the message list for the API call.

        Args:
            tool_completion (bool, optional): Indicates whether the message is for a tool-assisted completion.
                Defaults to False.

        Returns:
            dict[str, str]: A dictionary representing the system message with 'content', 'role', and 'name' keys.
        """
        if not tool_completion and self.rag_enabled:
            rag_content: str = self.pinecone_handler.search_content()
            self.logger.info(f"RAG content: {rag_content}")
            content = (
                f"You are '{self.name}' and this is additional context: {rag_content}. "
                "Assist according to your role."
            )
        else:
            content = f"You are '{self.name}'. Assist according to your role."
        return {"content": content, "role": "system", "name": self.name}

    @staticmethod
    def fill_chat_completion_message_params(messages: list[Message]) -> list[dict]:
        """
        Convert a list of Message objects to a list of chat completion messages for use with the AzureOpenAI API.

        Args:
            messages (list[Message]): A list of Message objects to convert.

        Returns:
            list[dict]: A list of chat completion messages, as a dict ready for API usage.
        """
        messages_list_dict: list[dict] = []
        for message in messages:
            messages_list_dict.append(
                {
                    "content": message.content,
                    "role": message.role,
                    "name": message.name,
                    "pending_user_reply": message.pending_user_reply,
                    "datetime_value": message.datetime_value,
                }
            )
        return messages_list_dict


class MilvusHandler:
    """
    Handler of the Milvus API.
    """

    def __init__(self, raci_agent: OpenAIRaciAgent):
        self.logger: Logger = logging_config.get_logger(__name__)
        self.raci_agent: RaciAgent = raci_agent
        self.milvus_client: MilvusClient = MilvusClient()

    def search_content(self) -> str:
        """
        Search content using the Milvus client and return the concatenated results as a single string.

        Returns:
            str: A single string containing all the search results concatenated together.
        """
        content: str = ""
        results: list[str] = self.milvus_client.search(self.raci_agent.description)
        for result in results:
            content += result + " "
        return content


class PineconeHandler:
    """
    Handler of the Pinecone API.
    """

    def __init__(self, raci_agent: OpenAIRaciAgent):
        self.logger: Logger = logging_config.get_logger(__name__)
        self.raci_agent: RaciAgent = raci_agent
        api_key = os.getenv("PINECONE_API_KEY")
        region = os.getenv("PINECONE_REGION")
        index_name = os.getenv("PINECONE_INDEX_NAME")
        namespace = os.getenv("PINECONE_NAMESPACE")
        self.pinecone_client: PineconeClient = PineconeClient(
            api_key=api_key, region=region, index_name=index_name, namespace=namespace
        )
        # self.conversation = None
        self.messages = None

    def search_content(self) -> str:
        """
        Search content using the Pinecone client with both agent description and conversation context,
        and return the concatenated results as a single string.

        Returns:
            str: A single string containing all the search results concatenated together.
        """
        # Combine description and conversation context for a more comprehensive search query
        oai_messages: list[dict] = self.extract_message_content(self.messages)
        combined_query = f"{self.raci_agent.description} {oai_messages}"

        content: str = ""
        results: list[str] = self.pinecone_client.search(combined_query)
        for result in results:
            content += result + " "
        return content

    @staticmethod
    def extract_message_content(messages: list[Message]) -> list[dict]:
        """
        Convert a list of Message objects to a string of all content part of chat completion messages.

        Args:
            messages (list[Message]): A list of Message objects to convert.

        Returns:
            string : A string of all content part of chat completion messages.
        """
        messages_list: list = []
        for message in messages:
            messages_list.append(message.content)
        messages_str = "\n".join(messages_list)
        return messages_str
