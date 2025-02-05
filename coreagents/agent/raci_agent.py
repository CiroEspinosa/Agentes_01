"""
Author: Anton Pastoriza
"""
import json
import sys
import threading
import time
from logging import Logger
from typing import Optional

import confluent_kafka
import uvicorn
from confluent_kafka import Consumer, Producer, KafkaException, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
from fastapi import APIRouter, FastAPI
from redis import Redis, RedisError

from factory import web_factory
from model.protocol import Conversation, Message
from utils import logging_config
from utils import protocol_utils


class RaciAgent:
    """
    A class representing an agent. The agent communicates through Kafka and REST API,
    and manages data storage using a Cache.

    Attributes:
        name (str): The name of the agent.
        description (str): A brief description of the agent.
        kafka_handler (KafkaHandler): Handler for Kafka messaging.
        web_handler (WebHandler): Handler for web server interactions.
        redis_handler (RedisHandler): Handler for Redis data storage.
    """

    def __init__(self, name: str, description: str, http_port: int = 9000):
        """
        Initialize a RaciAgent instance with the provided name, description, and HTTP port.

        Args:
            name (str): The name of the agent.
            description (str): A brief description of the agent.
            http_port (int): The port number for the HTTP server. Defaults to 9000.
        """
        self.logger: Logger = logging_config.get_logger(__name__)
        self.name: str = name
        self.description = description
        self.kafka_handler: KafkaHandler = KafkaHandler(self)
        self.web_handler: WebHandler = WebHandler(self, http_port)
        self.redis_handler: RedisHandler = RedisHandler(self)

    def add_api_routes(self, router: APIRouter) -> None:
        """
        To override when needed. Add additional API routes to the FastAPI router.

        Args:
            router (APIRouter): The router to which API routes are added.
        """
        self.logger.info(f"No additional API routes added to router: {router.routes}.")

    async def chat(self, request: dict) -> dict:
        """
        Handles a single dummy chat interaction for the assistant, taking a user request,
        processing it to generate a echo response in chat completion format.

        Args:
            request (dict): A dictionary containing the request details, expected to have
                            keys that map to `Message` attributes such as 'content', 'role',
                            and 'name'. This represents the user's input message.

        Returns:
            dict: A dictionary representing the echo response from the assistant, containing keys like
                  'content' (the echo reply), 'role' (set to 'dummy'), and 'name' (set to the agent name).

        """
        self.logger.info("Dummy chat of '%s'", self.name)
        return {
            "content": request,
            "role": "dummy",
            "name": self.name
        }

    async def health(self) -> dict:
        """
        Health check endpoint for the web server.

        Returns:
            dict: A dictionary containing the agent's name and current thread information.
        """
        self.logger.info("Checked status of '%s'", self.name)

        return {
            "agent": self.name,
            "thread": f"{threading.current_thread().name}",
            "topic-consumer": self.kafka_handler.consumer.list_topics()
        }

    def send_message(self, agent_identifier: str, conversation: Conversation) -> None:
        """
        Send a conversation message to a specific agent through Kafka.

        Args:
            agent_identifier (str): The identifier of the target agent.
            conversation (Conversation): The conversation object to send.
        """
        topic_identifier = f"topic-{agent_identifier}"
        self.logger.info("Sending from: '%s' to queue: '%s'", conversation.header.sender, topic_identifier)
        conversation_dict: dict = protocol_utils.to_dict_conversation(conversation)
        self.kafka_handler.send_message(topic_identifier, conversation_dict)

    def store_conversation(self, user_id: str, conversation_id: str, conversation: Conversation) -> int:
        """
        Store a conversation in the cache.

        Args:
            user_id (str): The user ID associated with the conversation.
            conversation_id (str): The conversation ID.
            conversation (Conversation): The conversation object to store.

        Returns:
            int: The number of fields added to the Redis store.
        """
        key: str = f"{user_id}:{conversation_id}"
        conversation_dict: dict = protocol_utils.to_dict_conversation(conversation)
        self.logger.debug("Storing conversation for key '%s': %s", key, conversation_dict)
        return self.redis_handler.store(key, conversation_dict)

    def retrieve_conversation(self, user_id: str, conversation_id: str) -> Conversation:
        """
        Retrieve a conversation from the cache.

        Args:
            user_id (str): The user ID associated with the conversation.
            conversation_id (str): The conversation ID.

        Returns:
            Conversation: The retrieved conversation object.
        """
        key: str = f"{user_id}:{conversation_id}"
        conversation_dict: dict = self.redis_handler.retrieve(key)
        self.logger.debug("Retrieved conversation for key '%s': %s", key, conversation_dict)
        conversation: Conversation = protocol_utils.to_conversation_from_dict(conversation_dict)
        return conversation

    def start(self) -> None:
        """
        Start the agent by initializing Kafka, web, and cache handlers.
        """
        self.kafka_handler.start()
        self.web_handler.start()
        self.redis_handler.start()

    def on_response(self, response: dict) -> None:
        """
        Process a response received from Kafka.

        Args:
            response (dict): The response data received from Kafka.
        """
        if response["header"] is not None:
            if response["messages"] is not None:
                conversation: Conversation = protocol_utils.to_conversation_from_dict(response)
                self.logger.info("From: '%s' To: %s", conversation.header.sender, self.name)
                self.process_response(conversation)
            else:
                self.logger.debug("No messages in response to se agent '%s'", self.name)
        else:
            self.logger.debug("No header in response to se agent '%s'", self.name)

    def process_response(self, conversation: Conversation):
        """
        To override when needed. Default processing of a conversation response.

        Args:
            conversation (Conversation): The conversation to process.
        """
        self.logger.debug("Default processing %s", conversation.header.conversation_id)


class KafkaHandler:
    """
    A class to handle Kafka messaging for the RaciAgent.

    This class provides methods to set up Kafka connections, send and receive messages, and manage
    Kafka topics for the associated RaciAgent.

    Attributes:
        raci_agent (RaciAgent): The RaciAgent instance associated with this handler.
        consumer (Optional[Consumer]): Kafka consumer instance for receiving messages.
        producer (Optional[Producer]): Kafka producer instance for sending messages.
        running (bool): Flag indicating whether the Kafka handler is currently running.
        logger (Logger): Logger instance for logging events and errors.
    """

    ERROR_UNKNOWN_TOPIC: int = -188
    ERROR_UNKNOWN_PARTITION: int = -190
    ERROR_PARTITION_EOF: int = -191

    def __init__(self, raci_agent: RaciAgent):
        """
        Initialize a KafkaHandler instance.

        This sets up the initial attributes but does not establish a Kafka connection.

        Args:
            raci_agent (RaciAgent): The RaciAgent instance this handler is associated with.
        """
        self.logger: Logger = logging_config.get_logger(__name__)
        self.raci_agent = raci_agent
        # Kafka related attributes
        self.running = False
        self.consumer: Optional[Consumer] = None
        self.producer: Optional[Producer] = None

    def setup_connection(self):
        """
        Set up the connection to the Kafka server, including the consumer and producer.

        This method initializes the Kafka consumer and producer, creates a Kafka topic
        if it doesn't already exist, and subscribes the consumer to the appropriate topic.
        It also sets the `running` flag to True to indicate that the handler is ready to process messages.

        Raises:
            KafkaException: If there is an issue setting up the Kafka connection.
        """
        try:
            self.consumer = Consumer({
                "bootstrap.servers": "kafka:29092",
                "group.id": 'node-1-group',
                "auto.offset.reset": 'earliest'
            })

            self._create_topic("kafka:29092")
            self.producer = Producer({"bootstrap.servers": "kafka:29092"})
            self.consumer.subscribe([f"topic-{self.raci_agent.name}"])
            self.running = True
            self.logger.info("'%s' successfully connected", self.raci_agent.name)
        except KafkaException as e:
            self.logger.error("'%s' Connection failed. Error: %s", self.raci_agent.name, e)

    def delivery_report(self, err: Optional[KafkaError], msg: confluent_kafka.Message):
        """
        Callback function to report the delivery status of a message.

        This function is called when a message is sent via the Kafka producer. It logs
        whether the message was successfully delivered or if there was an error.

        Args:
            err (Optional[KafkaError]): The error object if the message delivery failed.
            msg (Message): The message that was attempted to be sent.
        """
        if err is not None:
            self.logger.error("Node '%s': Message delivery failed: %s", self.raci_agent.name, err)
        else:
            self.logger.debug("Node '%s': Message delivered to '%s' [%s]", self.raci_agent.name, msg.topic(), msg.partition())

    def poll_messages(self):
        """
        Poll for messages from Kafka and process them.

        This method continuously polls Kafka for new messages. If a message is received,
        it processes the message by passing it to the `on_response` method of the associated
        RaciAgent. If an error occurs during polling, it attempts to reconnect to Kafka.
        """
        try:
            message: dict = self._poll_message()
            if message is None:
                self.logger.debug("No message while consuming from '%s'", self.raci_agent.name)
            else:
                self.raci_agent.on_response(message)
        except KafkaException as e:
            self.logger.debug("Polling error on Node '%s': %s", self.raci_agent.name, e)
            self.setup_connection()

    def send_message(self, topic_identifier: str, message: dict):
        """
        Send a message to a Kafka topic.

        This method serializes a dictionary message into a JSON string and sends it to the
        specified Kafka topic using the Kafka producer.

        Args:
            topic_identifier (str): The Kafka topic to send the message to.
            message (dict): The message data to send.
        """
        try:
            payload = json.dumps(message)
            self.producer.produce(topic_identifier, value=payload, callback=self.delivery_report)
            self.producer.flush()
        except AttributeError as error:
            print(f"Error: Kafka producer is not initialized. {error}", file=sys.stderr)
            sys.exit(1)
        except Exception as error:
            print(f"Unexpected error while sending message: {error}", file=sys.stderr)
            sys.exit(1)

    def start(self):
        """
        Start the Kafka handler by setting up the connection and beginning the message polling.
        """
        self.setup_connection()
        threading.Thread(target=self.run_kafka).start()

    def run_kafka(self):
        """
        Run the Kafka message polling in a separate thread.

        This method runs in a loop, continuously polling Kafka for messages. When the
        running flag is set to False, it gracefully shuts down the Kafka consumer.
        """
        try:
            while self.running:
                self.poll_messages()
        finally:
            if self.consumer:
                self.consumer.close()
            self.logger.warning("Node '%s': Shutting down gracefully", self.raci_agent.name)

    def _create_topic(self, bootstrap_servers: str):
        """
        Create a Kafka topic if it doesn't already exist.

        This method uses the Kafka AdminClient to check if a topic with the name based on
        the RaciAgent's name exists. If not, it creates the topic with one partition and
        a replication factor of one.

        Args:
            bootstrap_servers (str): The Kafka bootstrap servers to connect to.
        """
        topic_name: str = f"topic-{self.raci_agent.name}"
        admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})

        # Check if the topic already exists
        existing_topics = admin_client.list_topics(timeout=10).topics

        if topic_name in existing_topics:
            self.logger.info("Topic '%s' already exists", topic_name)
        else:
            self.logger.info(f"Creating topic {topic_name}")

            # Create the topic if it doesn't exist
            topic_list = [NewTopic(topic_name, num_partitions=1, replication_factor=1)]
            fs: dict = admin_client.create_topics(topic_list)

            # Wait for operation to finish
            for topic, f in fs.items():
                self.logger.debug("Waiting for topic '%s'...", topic)
                try:
                    f.result()  # The result itself is None
                    self.logger.info("Topic '%s' created successfully", topic_name)
                except Exception as e:
                    self.logger.error("Failed to create topic '%s': %s", topic_name, e)

    def _poll_message(self, retries: int = 15, delay: int = 3) -> dict:
        """
        Poll a message from Kafka with retry logic.

        This method attempts to poll a message from the Kafka consumer. If no message is received,
        it retries a specified number of times with a delay between attempts. It processes the
        message if successfully polled.

        Args:
            retries (int): The number of times to retry polling if no message is received.
            delay (int): The delay in seconds between retry attempts.

        Returns:
            dict: The message data if successfully polled, otherwise None.
        """
        msg: confluent_kafka.Message = self.consumer.poll(1.0)
        message: Optional[dict] = None
        polled_message: bool = False
        total_retries: int = 0

        while not polled_message and total_retries < retries:
            if msg is None:
                self.logger.debug("No message while consuming from '%s'", self.raci_agent.name)
                polled_message = True
            else:
                error_message: Optional[KafkaError] = msg.error()
                if error_message and error_message.code() != KafkaHandler.ERROR_UNKNOWN_TOPIC:
                    self.logger.error("Node '%s': Topic not available yet? %s", self.raci_agent.name, msg.error())
                if error_message and error_message.code() != KafkaHandler.ERROR_UNKNOWN_PARTITION:
                    self.logger.error("Node '%s': Partition not available yet? %s", self.raci_agent.name, msg.error())
                elif error_message and error_message.code() != KafkaHandler.ERROR_PARTITION_EOF:
                    self.logger.error("Node '%s': %s", self.raci_agent.name, msg.error())
                else:
                    message_value = msg.value()
                    if message_value is not None:
                        message_value_decoded: str = message_value.decode("utf-8")
                        message: dict = json.loads(message_value_decoded)
                        self.logger.debug("Node '%s': Consumed message from 'topic-%s': %s", self.raci_agent.name, self.raci_agent.name, message)
                        self.consumer.commit(message=msg)
                        polled_message = True

            total_retries += 1
            if not polled_message and total_retries < retries - 1:
                self.logger.info(f"Retrying '{self.raci_agent.name}' in {delay} seconds...")
                time.sleep(delay)

        return message


class RedisHandler:
    """
    A class to handle Redis cache interactions for the RaciAgent.

    Attributes:
        raci_agent (RaciAgent): The RaciAgent instance associated with this handler.
        r (Optional[Redis]): The Redis connection instance.
    """

    def __init__(self, raci_agent: RaciAgent):
        """
        Initialize a RedisHandler instance.

        Args:
            raci_agent (RaciAgent): The RaciAgent instance this handler is associated with.
        """
        self.logger: Logger = logging_config.get_logger(__name__)
        self.r: Optional[Redis] = None
        self.raci_agent = raci_agent

    def _setup_redis(self, host: str = "redis", port: int = 6379):
        """
        Set up the connection to the Redis server.
        """
        self.r = Redis(
            host=host,
            port=port,
            decode_responses=True
        )
        self.logger.info("Redis connection established at %s:%d", host, port)

    def store(self, key: str, value: dict) -> int:
        """
        Store a value in Redis.

        Args:
            key (str): The key under which the value is stored.
            value (dict): The value to store.

        Returns:
            int: The number of fields added to the Redis store.
        """
        added_fields: int = 0
        try:
            if value is not None:
                serialized_value: str = json.dumps(value)
                added_fields = self.r.set(key, serialized_value)
        except (RedisError, TypeError) as e:
            self.logger.error("Failed to store value in Redis: %s", e)

        if added_fields == 0:
            self.logger.warning("No value stored in Redis for key '%s'", key)
        return added_fields

    def retrieve(self, key: str) -> dict:
        """
        Retrieve a value from Redis.

        Args:
            key (str): The key of the value to retrieve.

        Returns:
            dict: The retrieved value.
        """
        value: dict = {}

        try:
            serialized_value: str = self.r.get(key)
            if serialized_value is not None:
                value = json.loads(serialized_value)
            else:
                self.logger.error("No value found in Redis for key: %s", key)
        except (RedisError, json.JSONDecodeError) as e:
            self.logger.error("Failed to retrieve value from Redis: %s", e)

        return value

    def delete(self, key: str) -> bool:
        """
        Delete a value from Redis.

        Args:
            key (str): The key of the value to delete.

        Returns:
            bool: True if the key was deleted, False otherwise.
        """
        deleted: bool = False
        try:
            result: int = self.r.delete(key)
            deleted = result == 1
        except RedisError as e:
            self.logger.error("Failed to delete key from Redis: %s", e)
        return deleted

    def start(self):
        """
        Start the Redis handler by setting up the Redis connection.
        """
        self._setup_redis()


class WebHandler:
    """
    A class to handle the web server for the RaciAgent, using FastAPI.

    Attributes:
        raci_agent (RaciAgent): The RaciAgent instance associated with this handler.
        http_port (int): The port number on which the HTTP server will run.
        app (Optional[FastAPI]): The FastAPI application instance.
        router (Optional[APIRouter]): The API router for handling requests.
    """

    def __init__(self, raci_agent: RaciAgent, http_port: int):
        """
        Initialize a WebHandler instance.

        Args:
            raci_agent (RaciAgent): The RaciAgent instance this handler is associated with.
            http_port (int): The port number for the HTTP server.
        """
        self.logger: Logger = logging_config.get_logger(__name__)
        self.raci_agent = raci_agent
        self.http_port = http_port
        self.app: Optional[FastAPI] = None
        self.router: Optional[APIRouter] = None

    def _setup_web(self):
        """
        Set up the FastAPI application, including CORS middleware and routes.
        """
        self.app = web_factory.create_app()
        self.router = APIRouter()
        self.router.add_api_route("/chat", self.raci_agent.chat, methods=["POST"])
        self.router.add_api_route("/health", self.raci_agent.health, methods=["GET"])
        self.raci_agent.add_api_routes(self.router)
        self.app.include_router(self.router)

    def start(self):
        """
        Start the web server by setting up the FastAPI application and running it in a separate thread.
        """
        self._setup_web()
        threading.Thread(target=self._run_web_server).start()

    def _run_web_server(self):
        """
        Run the FastAPI web server.
        """
        uvicorn.run(self.app, host="0.0.0.0", port=self.http_port)
