"""
Author: Anton Pastoriza
"""
from datetime import datetime
from typing import Optional, override

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam

from agent.oai.oai_raci_agent import OpenAIRaciAgent
from agent.helper import swarm_master_helper
from config.llm import ModelConfig
from model.protocol import Message, Conversation
from model.vo import AgentVO


class SwarmMaster(OpenAIRaciAgent):
    def __init__(self, name: str, description: str, model_config: ModelConfig, agent_vos: list[AgentVO], http_port: int = 9100):
        super().__init__(name, description, model_config, http_port)
        self.agent_vos = agent_vos
        self.responsible_agent = swarm_master_helper.identify_single_role_agent(self.agent_vos, "r")
        self.accountable_agent = swarm_master_helper.identify_single_role_agent(self.agent_vos, "a")
        self.proxy = None

    @override
    def process_response(self, conversation: Conversation):
        # when conversation is empty or conversation has a single user message, conversation must be framed
        if len(conversation.messages) == 0:
            system_message: Message = swarm_master_helper.compose_initial_system_message(self.name, self.agent_vos)
            conversation.messages.append(system_message)
        elif len(conversation.messages) == 1:
            message: Message = conversation.messages[0]
            if message.role == "user":
                system_message: Message = swarm_master_helper.compose_initial_system_message(self.name, self.agent_vos)
                conversation.messages.append(system_message)
        self._process_regular_response(conversation)

    def _process_regular_response(self, conversation: Conversation):
        agent_requestor: str = conversation.header.sender
        self.logger.debug("Processing %s from %s", conversation, agent_requestor)

        next_agent: str = self._identify_next_agent(agent_requestor, conversation.messages)
        self.logger.info("req: %s, next: %s", agent_requestor, next_agent)
        if self.proxy is None:
            self.proxy = agent_requestor
        if self.proxy == next_agent and conversation.messages[-1].role != 'user':
            conversation.messages[-1].pending_user_reply = True
        conversation.messages[-1].datetime_value = datetime.now().timestamp()
        conversation.header.sender = self.name
        self.store_conversation(conversation.header.user_id, conversation.header.conversation_id, conversation)

        self.logger.debug("From %s to %s", agent_requestor, next_agent)
        self.send_message(next_agent, conversation)

    def _identify_next_agent(self, previous_agent: str, messages: list[Message]) -> str:
        retries: int = 0
        agent_identified: bool = False
        next_agent: Optional[str] = None
        while not agent_identified and retries < 5:
            completed_agent_identified = self._complete_next_agent(previous_agent, messages, (retries > 0))
            if self._is_in_agents_list(completed_agent_identified):
                next_agent = completed_agent_identified
                agent_identified = True
            else:
                self.logger.error("Next Agent not identified. Previous Agent: %s", previous_agent)
                retries += 1

        self.logger.info("Next agent: %s", next_agent)
        if not agent_identified:
            next_agent = self.responsible_agent.identifier
        return next_agent

    def _complete_next_agent(self, previous_agent: str, messages: list[Message], exclude_previous_agents: bool = False) -> str:
        oai_messages: list[dict] = self.fill_chat_completion_message_params(messages)
        content: str = ""
        if exclude_previous_agents:
            agent_vos_filtered: list[AgentVO] = [agent_vo for agent_vo in self.agent_vos if agent_vo.identifier not in [msg.name for msg in messages]]
            self.logger.debug("Reducing agent_list to: %s", agent_vos_filtered)
            content = swarm_master_helper.compose_next_agent_message_content(agent_vos_filtered, previous_agent)
        else:
            content = swarm_master_helper.compose_next_agent_message_content(self.agent_vos, previous_agent)

        oai_messages.append({
            "content": content,
            "role": "system",
            "name": self.name,
            #"pending_user_reply": False
        })

        response = self.client.chat.completions.create(
            model=self.model_config.model,
            messages=oai_messages,
            temperature=self.model_config.randomness,
            stream=False,
            max_tokens=self.model_config.max_tokens
        )
        next_agent = response.choices[0].message.content
        return next_agent

    def _is_in_agents_list(self, agent_to_validate: str) -> bool:
        is_listed: bool = False
        i: int = 0
        while i < len(self.agent_vos) and not is_listed:
            if agent_to_validate == self.agent_vos[i].identifier:
                is_listed = True
            else:
                i += 1
        return is_listed
