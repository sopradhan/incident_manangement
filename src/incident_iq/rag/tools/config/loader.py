import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    """
    Lazy-loading config with JSON and caching.
    Configuration Loader - JSON-only, optimized with lazy loading and caching.
    Loads specific config values on-demand from JSON files.
    """

    _config_dir: Optional[str] = None
    _cache: Dict[str, Any] = {}

    @classmethod
    def set_config_dir(cls, config_dir: str) -> None:
        """Set base config directory"""
        cls._config_dir = config_dir
        cls._cache.clear()

    @classmethod
    def _load_json_file(cls, filename: str) -> Dict[str, Any]:
        """Load single JSON file and cache result"""
        if filename in cls._cache:
            return cls._cache[filename]

        if not cls._config_dir:
            raise ValueError("Config directory not set. Call set_config_dir() first")

        file_path = Path(cls._config_dir) / filename
        if not file_path.exists():
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        cls._cache[filename] = config
        return config

    @classmethod
    def get_system_prompt(cls, agent_name: str) -> str:
        """Get specific agent system prompt (lazy load)"""
        config = cls._load_json_file('prompts_config.json')
        prompt = config.get(agent_name, {}).get('system_prompt', '')
        return prompt.strip() if prompt else ''

    @classmethod
    def get_llm_config(cls, llm_name: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM configuration"""
        config = cls._load_json_file('llm_config.json')
        if llm_name:
            return config.get(llm_name, {})
        return config

    @classmethod
    def get_agent_config(cls, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get agent configuration"""
        config = cls._load_json_file('agent_config.json')
        if agent_name:
            return config.get(agent_name, {})
        return config

    @classmethod
    def get_rbac_config(cls) -> Dict[str, Any]:
        """Get RBAC configuration"""
        return cls._load_json_file('rbac_config.json')

    @classmethod
    def get_data_sources_config(cls) -> Dict[str, Any]:
        """Get data sources configuration"""
        return cls._load_json_file('data_sources.json')

    @classmethod
    def get_system_config(cls) -> Dict[str, Any]:
        """Get system configuration"""
        return cls._load_json_file('system_config.json')

    @classmethod
    def get_prompt_template(cls, category: str, template_name: str) -> str:
        """Get specific prompt template by category and name"""
        config = cls._load_json_file('prompts_config.json')
        template = config.get(category, {}).get(template_name, {}).get('template', '')
        return template.strip() if template else ''

    @classmethod
    def get_rbac_namespace(cls, namespace_name: str) -> Dict[str, Any]:
        """Get specific RBAC namespace config"""
        config = cls._load_json_file('rbac_config.json')
        return config.get('namespaces', {}).get(namespace_name, {})

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached configs"""
        cls._cache.clear()