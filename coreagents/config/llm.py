"""
Author: Anton Pastoriza
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ModelConfig:
    """
    A class representing the configuration for a model, including its API key and base URL.

    Attributes:
        model (str): The name or identifier of the model.
        api_key (str): The API key used to authenticate requests to the model.
        base_url (str): The base URL for accessing the model's API.
    """
    model: str
    api_key: str
    base_url: str
    max_tokens: int
    randomness: float
    api_version: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        """
        Create a ModelConfig object from a dictionary.

        Args:
            data (Dict[str, Any]): A dictionary containing model configuration data.

        Returns:
            ModelConfig: A ModelConfig object created from the provided dictionary.
        """
        return cls(
            model=data.get("model", ""),
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            max_tokens=data.get("max_tokens", 0),
            randomness=data.get("randomness", 0.0),
            api_version=data.get("api_version", "")
        )
