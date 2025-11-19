import requests

from base_llm import BaseLLM
from typing import Any, Dict, List

class OllamaLLM(BaseLLM):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get("model", "llama2")
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.http = requests.Session()

    def generate(self, prompt: str, **kwargs) -> str:
        resp = self.http.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "temperature": kwargs.get("temperature", self.temperature),
                "stream": False
            }
        )
        resp.raise_for_status()
        return resp.json()["response"]

    def embed(self, text: str) -> List[float]:
        resp = self.http.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model, "prompt": text}
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
