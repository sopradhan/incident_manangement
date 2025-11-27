"""RAG Agents - Multiple implementations for different orchestration patterns."""
from .langgraph_agent import LangGraphRAGAgent

# Try to import DeepAgentsRAGAgent; it's optional if deepagents is not installed
try:
    from .deepagents_agent import DeepAgentsRAGAgent
    __all__ = ["LangGraphRAGAgent", "DeepAgentsRAGAgent"]
except ImportError as e:
    print(f"INFO: DeepAgentsRAGAgent not available ({str(e)}). Using LangGraphRAGAgent only.")
    DeepAgentsRAGAgent = None
    __all__ = ["LangGraphRAGAgent"]
