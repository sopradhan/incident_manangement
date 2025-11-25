"""
Centralized configuration loader for the incident_iq package
Reads from pyproject.toml [tool.incident-iq] section
"""
import tomllib
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for incident_iq"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        """Singleton pattern - ensure only one config instance"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self) -> None:
        """Load configuration from pyproject.toml"""
        try:
            config_file = self._find_config_file()
            if config_file:
                with open(config_file, 'rb') as f:
                    full_config = tomllib.load(f)
                self._config = full_config.get('tool', {}).get('incident-iq', {})
                print(f"Configuration loaded from {config_file}")
            else:
                print("Warning: pyproject.toml not found, using defaults")
                self._config = {}
        except Exception as e:
            print(f"Warning: Failed to load configuration: {e}")
            self._config = {}
    
    @staticmethod
    def _find_config_file() -> Optional[Path]:
        """Find pyproject.toml by traversing up from this file"""
        current_dir = Path(__file__).parent
        
        # Try up to 10 levels up
        for _ in range(10):
            config_file = current_dir / 'pyproject.toml'
            if config_file.exists():
                return config_file
            current_dir = current_dir.parent
        
        return None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def get_nested(self, path: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation
        
        Example: config.get_nested('database.dir', 'data')
        """
        keys = path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        
        return value if value is not None else default
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self._config.copy()


def get_config() -> Config:
    """Get the singleton config instance"""
    return Config()


# Convenience functions for common config values
def get_database_dir() -> str:
    """Get database directory name from config"""
    return get_config().get('database-dir', 'data')


def get_database_name() -> str:
    """Get database filename from config"""
    return get_config().get('database-name', 'incident_iq.db')


def get_vector_db_dir() -> str:
    """Get vector database directory from config"""
    return get_config().get('vector-db-dir', 'data/chroma_db')
