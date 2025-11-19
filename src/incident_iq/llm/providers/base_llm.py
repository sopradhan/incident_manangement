from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseLLM(ABC):
    """Base class for all LLM providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        pass