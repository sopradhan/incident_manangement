import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class EnvConfig:
    """Load configuration from environment variables"""
    
    @staticmethod
    def get_db_path() -> str:
        # FIXED: Use optimized RAG schema in chroma_db/rag.db, not old incident_iq.db
        return os.getenv('DB_PATH', 'chroma_db/rag.db')
    
    @staticmethod
    def get_chroma_db_path() -> str:
        return os.getenv('CHROMA_DB_PATH', 'chroma_db')
    
    @staticmethod
    def get_rag_config_path() -> str:
        return os.getenv('RAG_CONFIG_PATH', 'src/incident_iq/rag/config')
    
    @staticmethod
    def get_app_env() -> str:
        return os.getenv('APP_ENV', 'development')
    
    @staticmethod
    def get_log_level() -> str:
        return os.getenv('LOG_LEVEL', 'info')
