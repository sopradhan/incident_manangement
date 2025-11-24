"""Simple prompt loader utility - loads all prompts from JSON config"""
import json
from pathlib import Path


class PromptLoader:
    """Load and format prompts from JSON configuration"""
    
    _config = None
    _config_path = Path(__file__).parent / "prompts.json"
    
    @classmethod
    def load_config(cls):
        """Load config once and cache it"""
        if cls._config is None:
            with open(cls._config_path, 'r') as f:
                cls._config = json.load(f)
        return cls._config
    
    @classmethod
    def get_system_prompt(cls, agent_name: str) -> str:
        """Get system prompt for agent"""
        config = cls.load_config()
        return config.get('system_prompts', {}).get(agent_name, '')
    
    @classmethod
    def get_prompt(cls, category: str, prompt_name: str) -> dict:
        """Get prompt template by category and name"""
        config = cls.load_config()
        return config.get(category, {}).get(prompt_name, {})
    
    @classmethod
    def format_prompt(cls, category: str, prompt_name: str, **kwargs) -> str:
        """Get and format prompt template with variables"""
        prompt_config = cls.get_prompt(category, prompt_name)
        template = prompt_config.get('prompt', '')
        if not template:
            return ''
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"Warning: Missing variable {e} for prompt {category}/{prompt_name}")
            return template
