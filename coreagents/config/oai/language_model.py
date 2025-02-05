"""
Author: Anton Pastoriza
"""

from config.llm import ModelConfig
import os


def model_config(model: str = "gpt-4o", max_tokens: int = 16000, randomness: float = 0.0) -> ModelConfig:
    """
    Create a ModelConfig object with predefined settings.

    Returns:
        ModelConfig: A ModelConfig object with predefined model name, API key, and base URL.
    """
    return ModelConfig(
        model=model,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_BASE_URL"),
        max_tokens=max_tokens,
        randomness=randomness,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
