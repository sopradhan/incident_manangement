from typing import List
from incident_iq.llm.utils.llm_config_loader import LLMConfigLoader
from incident_iq.llm.utils.llm_factory import LLMFactory


class LLMService:
    def __init__(self, config_path: str = "llm_config.yaml"):
        cfg = LLMConfigLoader.load(config_path)

        # Load LLM provider
        provider_name = cfg.get("default_provider")
        provider_cfg = cfg["llm_providers"][provider_name]

        self.llm = LLMFactory.build_llm(provider_name, provider_cfg)

        # Load embedding provider
        embed_name = cfg.get("default_embedding_provider")
        embed_cfg = cfg["embedding_providers"][embed_name]

        self.embedder = LLMFactory.build_embedding(embed_name, embed_cfg)

    # -------------- High-level API -----------------

    def generate(self, prompt: str) -> str:
        return self.llm.generate(prompt)

    def embed(self, text: str) -> List[float]:
        return self.embedder.embed(text)
