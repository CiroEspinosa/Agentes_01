"""
Author: Anton Pastoriza
"""

import uuid
from datetime import datetime
from typing import override

from fastapi import APIRouter

import openai
import json
import openai
from typing import override, Optional
from dataclasses import asdict
from fastapi import APIRouter, HTTPException
from agent.oai.oai_raci_agent import OpenAIRaciAgent
from config.oai.language_model import model_config
from model.protocol import InitialMessage, Conversation, Message, Header, ReplyMessage
from utils import datetime_helper


class UserProxyAgent(OpenAIRaciAgent):
    """
    A proxy agent class that extends the OpenAIRaciAgent to handle user interactions,
    including starting new conversations and processing responses in ongoing conversations.
    """

    @override
    def add_api_routes(self, router: APIRouter):
        """
        Extends the API routes for starting and retrieving conversations.

        Args:
            router (APIRouter): The FastAPI router to add the routes to.
        """
        router.add_api_route("/conversation", self.start_conversation, methods=["POST"])
        router.add_api_route("/conversation/{user_id}/{conversation_id}", self.conversation, methods=["GET"])
        router.add_api_route("/reply", self.reply, methods=["POST"])
        router.add_api_route("/recommendations/{swarm_type}/{user_id}", self.get_recommendations, methods=["GET"])

    async def get_recommendations(self, swarm_type:str, user_id: str, conversation_id: Optional[str] = ""):

        
        recommendations = []

        try:
            if not conversation_id and swarm_type == 'qr':
                recommendations = [
                    {"message": "Process a table", "example": "Process the call_center table."},
                    {"message": "Quality rules for a specific table", "example": "Generate quality rules for the catalog_sales table."},
                    {"message": "Quality rules for a specific task for a table", "example": "Specify the quality rules to validate that all mandatory fields in the call_center table are not empty."}
                ]
            elif not conversation_id and swarm_type == 'etl':
                recommendations = [
                    {"message": "ETL for customer behavior analysis", "example": "What percentage of customers have purchased on the website, broken down by education level?"},
                    {"message": "ETL for return rate calculation", "example": "I want to create an ETL process to calculate the percentage of returned products in 2001 by product type."},
                    {"message": "ETL for outlier detection in purchases", "example": "Extract the number of customers who have purchased 20 percentage above the mean."}
                ]
            else:
                #conver = await self.conversation(user_id,conversation_id)
                conver =self.retrieve_conversation(user_id, conversation_id)
                self.logger.info(f'Conver: {conver}')
                data = asdict(conver)
                json_data = json.dumps(data, indent=4)
                json_conver = json.loads(json_data)
                self.logger.info('JSON conver: ', json_conver)
                if json_conver != {}:
                    conversation = json_conver["messages"]
                    user_messages = [msg['content'] for msg in conversation if msg["role"] == "user"]
                    last_messages = user_messages[-10:]

                else:
                    print("The dictionary has no elements.")
                conversation_messages = [{"role": "user", "content": message} for message in last_messages]
                INSTRUCTIONS = f"""You are an agent responsible for suggesting the responses that the user could give when having a conversation with another agent.
                            The user is having a conversation with a technical support assistant.
                            You need to assume the role of the user and suggest responses that they could give in the current conversation.
                            You have access to the conversation history: {last_messages}. The history only includes the messages that the user has sent.
                            The technical support agent deals with the following topics:
                            - Data quality rule generation: Definition and application of rules that ensure the data meets quality standards defined by the user.
                            - Rule coding and testing: Implementation of the code for quality rules and development of unit tests in Python.
                            - Code review and quality assurance: Validation of code implementations and tests to comply with best practices and standards.
                            - Creation of ETL pipelines: generation of high-quality code to fulfill a functional requirement.
                            If the user is having a conversation about any of these topics, your suggestions should follow these guidelines: you need to generate 3 recommendations based on the messages in the history.
                            Do not generate recommendations about how to perform certain tasks.
                            The recommendations should be tasks within the above list.
                            These guidelines are based on the analysis of the message history, so depending on what the user has asked, you must follow the directions I have defined.
                            Your suggestions should be short and precise. Each suggestion should be as short as possible.
                            It is very important that you put yourself in the user's shoes; you need to generate recommendations as if you were the user.
                            The responses must be structured as a JSON array with each item containing a "message" and an "example" key. The "message" should be a short task or suggestion, and the "example" should provide an example of that task.
                            """
                if swarm_type == 'qr':
                    INSTRUCTIONS += """If the swarm type is qr taking examples like this: 
                            -Process the call_center table.,
                            -Generate quality rules for the catalog_sales table., 
                            -Specify the quality rules to validate that all mandatory fields in the call_center table are not empty.
                            """
                else:
                    INSTRUCTIONS += """If the swarm type is etl taking examples like this: 
                            -What percentage of customers have purchased on the website, broken down by education level?,
                            -I want to create an ETL process to calculate the percentage of returned products in 2001 by product type., 
                            -Extract the number of customers who have purchased 20 percentage above the mean.
                            """

                response_openai = self.client.chat.completions.create(
                    model=self.model_config.model,
                    messages=[
                        {"role": "system", "content": INSTRUCTIONS},
                        *conversation_messages
                    ],
                    temperature=self.model_config.randomness,
                    stream=False,
                    max_tokens=self.model_config.max_tokens
                )

                response_dict = response_openai.to_dict()
                recommendation_openai = response_openai.choices[0].message.content

                if recommendation_openai:
                    try:
                        if recommendation_openai.startswith("```json"):
                            recommendation_openai = recommendation_openai[7:].strip()
                            if recommendation_openai.endswith("```"):
                                recommendation_openai = recommendation_openai[:-3].strip()

                        self.logger.info(f"OpenAI response content: {recommendation_openai}")
                        recommendations_json = json.loads(recommendation_openai)

                        divided_recommendations = [
                            {"message": rec.get("message"), "example": rec.get("example")}
                            for rec in recommendations_json
                            if "message" in rec and "example" in rec
                        ]

                        recommendations = divided_recommendations[:3]
                        self.logger.info(f'Recommendations: {recommendations}')
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Error decoding JSON from OpenAI response: {e}")
                        raise ValueError("The OpenAI response does not have a valid JSON format.")
                else:
                    raise ValueError("The OpenAI response does not contain valid data.")

            return {"recommendations": recommendations}

        except Exception as e:
            self.logger.error("Error fetching recommendations: %s", e)
            raise HTTPException(status_code=500, detail="Error fetching recommendations")

    async def start_conversation(self, initial_message: InitialMessage) -> Conversation:
        """
        Starts a new conversation based on the initial message received.

        Args:
            initial_message (InitialMessage): The initial message containing the user's ID,
                                              swarm ID, and the request content.

        Returns:
            Conversation: The newly created conversation object.
        """
        swarm_id: str = initial_message.swarm
        user_id: str = initial_message.user
        request: str = initial_message.request
        pending_user_reply: bool = None
        datetime_value: str = datetime.now().timestamp()

        unique_id: uuid.UUID = uuid.uuid4()
        unique_id_str: str = str(unique_id)
        conversation_id: str = f"{user_id}_{unique_id_str}"

        header: Header = Header(
            user_id=user_id,
            conversation_id=conversation_id,
            sender=self.name
        )
        message: Message = Message(
            content=request,
            role="user",
            name=user_id,
            pending_user_reply=pending_user_reply,
            datetime_value=datetime_value
        )
        messages: list[Message] = [
            message
        ]
        conversation: Conversation = Conversation(
            header=header,
            messages=messages
        )
        self.logger.info("Started conversation with ID: '%s'", conversation_id)
        self.store_conversation(conversation.header.user_id, conversation.header.conversation_id, conversation)
        self.send_message(swarm_id, conversation)
        return conversation

    async def conversation(self, user_id: str, conversation_id: str) -> Conversation:
        """
        Retrieves an existing conversation by user ID and conversation ID.

        Args:
            user_id (str): The ID of the user involved in the conversation.
            conversation_id (str): The unique ID of the conversation.

        Returns:
            Conversation: The conversation object retrieved based on the provided IDs.
        """
        conversation: Conversation = self.retrieve_conversation(user_id, conversation_id)
        return conversation

    async def reply(self, reply_message: ReplyMessage) -> Conversation:
        """
        Reply an existing conversation of a user.

        Args:
           reply_message: The reply message coming from the user.

        Returns:
            Conversation: The conversation object retrieved based on the provided reply IDs.
        """

        conversation: Conversation = self.retrieve_conversation(reply_message.user_id, reply_message.conversation_id)
        message: Message = Message(
            content=reply_message.content,
            role="user",
            name=reply_message.user_id,
            pending_user_reply=None,
            datetime_value=datetime.now().timestamp()
        )
        conversation.messages.append(message)

        agent_requestor: str = conversation.header.sender

        conversation.header.sender = reply_message.user_id

        self.send_message(agent_requestor, conversation)
        return conversation

    @override
    def process_response(self, conversation: Conversation):
        """
        Stores the response for a given conversation by appending a response message
        and updating the conversation header.

        Args:
            conversation (Conversation): The conversation object containing the details
                                         of the conversation to process.
        """
        agent_requestor: str = conversation.header.sender
        self.logger.debug("Storing pending reply %s from '%s'", conversation, agent_requestor)
        self._store_pending_conversation_reply(conversation.header.conversation_id)

    def _store_pending_conversation_reply(self, conversation_id: str) -> int:
        """
        Store a pending conversation reply in the cache.

        Args:
            conversation_id (str): The conversation ID.

        Returns:
            int: The number of fields added to the Redis store.
        """
        key: str = f"pending-{conversation_id}"
        metadata_dict: dict = {
            "timestamp": datetime_helper.timestamp_now_as_str()
        }
        self.logger.debug("Storing pending conversation for key '%s': %s", key, metadata_dict)
        return self.redis_handler.store(key, metadata_dict)
