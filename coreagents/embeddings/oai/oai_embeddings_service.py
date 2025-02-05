"""
Author: Anton Pastoriza
"""

from openai import AzureOpenAI
from openai.types import CreateEmbeddingResponse, Embedding

from config.llm import ModelConfig
from config.oai.language_model import model_config
import os


class OAIEmbeddingsService:
    def __init__(self):
        gpt_embedding_engine = os.getenv("GPT_EMBEDDING_ENGINE")
        self.model_config: ModelConfig = model_config(gpt_embedding_engine)
        self.client = AzureOpenAI(
            api_key=self.model_config.api_key,
            api_version=self.model_config.api_version,
            azure_endpoint=self.model_config.base_url
        )

    def get_embeddings(self, text: str) -> list[float]:
        response: CreateEmbeddingResponse = self.client.embeddings.create(
            input=text,
            model=self.model_config.model
        )
        return response.data[0].embedding