from typing import Dict,Any

class LLMConfigLoader:
    @staticmethod
    def load(path: str = "config.yml") -> Dict[str, Any]:
        with open(path, "r") as f:
            return yaml.safe_load(f)