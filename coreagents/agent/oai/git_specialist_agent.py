from datetime import datetime
from typing import override

from openai.types.chat import ChatCompletion

from agent.oai.oai_raci_agent import OpenAIRaciAgent
from model.protocol import Conversation, Message
import requests
from pydantic import BaseModel, Field
from typing import Annotated


class UploadPyFileRequest(BaseModel):
    python_code: Annotated[str, Field(description="python code that is going to be uploaded into s3")]
    code_name: Annotated[str, Field(description="name of python code that is going to be uploaded into s3")]


class GitSpecialistAgent(OpenAIRaciAgent):

    @override
    def process_response(self, conversation: Conversation):
        """
        Process a conversation by generating a response using the OpenAI API.

        This method overrides the base class's process_response method to include
        AI-driven response generation.

        Args:
            conversation (Conversation): The conversation object to process.
        """
        agent_requestor: str = conversation.header.sender
        self.logger.debug("Processing %s from %s", conversation, agent_requestor)

        codes = {
            'programmer': self._get_codes(conversation.messages, True),
            'test': self._get_codes(conversation.messages, False)
        }
        programmer_code = str(codes.get('programmer')[1])
        programmer_code_name = str(codes.get('programmer')[0])
        test_code = str(codes.get('test')[1])
        test_code_name = str(codes.get('test')[0])
        code_upload_request = UploadPyFileRequest(python_code=programmer_code, code_name=programmer_code_name)
        test_code_upload_request = UploadPyFileRequest(python_code=test_code, code_name=test_code_name)
        response = "{"
        response += requests.post('http://tool-aws-s3:7121/api/upload-py/', code_upload_request.model_dump_json()).text
        response += requests.post('http://tool-aws-s3:7121/api/upload-py/',
                                  test_code_upload_request.model_dump_json()).text
        response += "}"
        response = response.replace("\"", "")


        conversation.messages.append(Message(
            content=str(response),
            role="assistant",
            name=self.name,
            pending_user_reply=False,
            datetime_value=datetime.now().timestamp()
        ))

        conversation.header.sender = self.name

        self.send_message(agent_requestor, conversation)

    def _get_codes(self, messages: list[Message], is_test: bool = True) -> list[str]:
        oai_messages: list[dict] = self.fill_chat_completion_message_params(messages)
        if not is_test:
            completion_message: dict[str, str] = {
                "content": "Identify the final code name and content given by qr-programmer and make it a ?@? separated list with those two values. Return ONLY the list and DO NOT provide a reason.",
                "role": "system",
                "name": self.name,
                "pending_user_reply": False
            }
        else:
            completion_message: dict[str, str] = {
                "content": "Identify the final code name and content given by qr-test-programmer and make it a ?@? separated list with those two values. Return ONLY the list and DO NOT provide a reason.",
                "role": "system",
                "name": self.name,
                "pending_user_reply": False
            }

        oai_messages.append(completion_message)
        response: ChatCompletion = self._do_completion_call(oai_messages)
        code_response: str = response.choices[0].message.content
        name_code, code = [item.strip() for item in code_response.split("?@?")]
        return [name_code, code]
