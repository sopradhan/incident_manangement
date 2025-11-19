from incident_iq.llm.providers.chat_ollama_provider import OllamaLLM
from typing import Any, Dict

class LLMFactory:
    """Factory class responsible for creating the right LLM instance."""

    PROVIDERS = {
        "ollama": OllamaLLM
    }

    EMBEDDING = {
        "ollama": OllamaLLM
    }

    @classmethod
    def build_llm(cls, provider: str, config: Dict[str, Any]):
        if provider not in cls.PROVIDERS:
            raise ValueError(f"Unknown LLM provider: {provider}")
        return cls.PROVIDERS[provider](config)

    @classmethod
    def build_embedding(cls, provider: str, config: Dict[str, Any]):
        if provider not in cls.EMBEDDING:
            raise ValueError(f"Unknown embedding provider: {provider}")
        return cls.EMBEDDING[provider](config)