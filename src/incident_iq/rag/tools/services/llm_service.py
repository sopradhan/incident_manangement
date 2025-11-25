"""
LLM Service - Multi-provider LLM abstraction
Supports: OpenAI, Anthropic, HuggingFace, Ollama
Token counting with tiktoken cache for performance
"""
import os
import json
from typing import List, Dict, Optional, Any
from functools import lru_cache
from langchain_core.language_models import BaseChatModel

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class LLMService:
    """Unified interface for multiple LLM providers"""
    
    def __init__(self, config: dict):
        """
        Initialize LLM service with configuration
        
        Args:
            config: Dictionary from llm_config.json
        """
        self.config = config
        self.provider = config.get('default_provider', 'openai')
        self.providers_config = config.get('llm_providers', {})
        self.embeddings_config = config.get('embedding_providers', {})
        
        self.llm = self._initialize_llm()
        self.embeddings = self._initialize_embeddings()
        
        print(f"[LLMService] Initialized with provider: {self.provider}")
    
    def _initialize_llm(self) -> BaseChatModel:
        """Initialize chat model based on configured provider"""
        provider_config = self.providers_config.get(self.provider, {})
        
        if not provider_config.get('enabled', False):
            # Find first enabled provider, checking HuggingFace first
            if self.providers_config.get('huggingface', {}).get('enabled', False):
                self.provider = 'huggingface'
                provider_config = self.providers_config['huggingface']
            else:
                # Try other providers
                for name, cfg in self.providers_config.items():
                    if name != 'huggingface' and cfg.get('enabled', False):
                        self.provider = name
                        provider_config = cfg
                        break
        
        try:
            if self.provider == 'openai':
                return self._create_openai(provider_config)
            elif self.provider == 'anthropic':
                return self._create_anthropic(provider_config)
            elif self.provider == 'huggingface':
                return self._create_huggingface(provider_config)
            elif self.provider == 'ollama':
                return self._create_ollama(provider_config)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            print(f"[ERROR] Failed to initialize {self.provider}: {e}")
            # Only fallback to Ollama if it's enabled and accessible
            if self.providers_config.get('ollama', {}).get('enabled', False):
                print("[INFO] Falling back to Ollama")
                try:
                    return self._create_ollama(self.providers_config.get('ollama', {}))
                except Exception as e2:
                    print(f"[ERROR] Ollama fallback also failed: {e2}")
                    raise e  # Raise original error
            else:
                raise  # Re-raise the original exception
    
    def _create_openai(self, config: dict) -> BaseChatModel:
        """Create OpenAI chat model"""
        from langchain_openai import ChatOpenAI
        
        api_key = os.getenv(config.get('api_key_env', 'OPENAI_API_KEY'))
        if not api_key:
            raise ValueError("OpenAI API key not found")
        
        return ChatOpenAI(
            model=config.get('model', 'gpt-4'),
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 2000),
            api_key=api_key
        )
    
    def _create_anthropic(self, config: dict) -> BaseChatModel:
        """Create Anthropic chat model"""
        from langchain_anthropic import ChatAnthropic
        
        api_key = os.getenv(config.get('api_key_env', 'ANTHROPIC_API_KEY'))
        if not api_key:
            raise ValueError("Anthropic API key not found")
        
        return ChatAnthropic(
            model=config.get('model', 'claude-3-sonnet-20240229'),
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 2000),
            api_key=api_key
        )
    
    def _create_huggingface(self, config: dict) -> BaseChatModel:
        """Create HuggingFace chat model using OpenAI-compatible API"""
        from langchain_openai import ChatOpenAI
        
        # Get API token from environment variable
        api_token = os.getenv('HUGGINGFACE_API_KEY') or os.getenv('HF_TOKEN')
        
        if not api_token:
            raise ValueError("HuggingFace API token not found in HUGGINGFACE_API_KEY or HF_TOKEN")
        
        # Use HuggingFace's router endpoint (OpenAI-compatible chat completions API)
        return ChatOpenAI(
            model=config.get('model', 'meta-llama/Llama-3.3-70B-Instruct'),
            base_url="https://router.huggingface.co/v1",
            api_key=api_token,
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 512)
        )
    
    def _create_ollama(self, config: dict) -> BaseChatModel:
        """Create Ollama chat model"""
        from langchain_ollama import ChatOllama
        
        return ChatOllama(
            model=config.get('model', 'gemma3:4b'),
            temperature=config.get('temperature', 0.3),
            base_url=config.get('base_url', 'http://localhost:11434')
        )
    
    def _initialize_embeddings(self):
        """Initialize embedding model"""
        default_provider = self.config.get('default_embedding_provider', 'sentence_transformers')
        embed_config = self.embeddings_config.get(default_provider, {})
        
        try:
            if default_provider == 'openai':
                from langchain_openai import OpenAIEmbeddings
                api_key = os.getenv(embed_config.get('api_key_env', 'OPENAI_API_KEY'))
                return OpenAIEmbeddings(
                    model=embed_config.get('model', 'text-embedding-3-small'),
                    api_key=api_key
                )
            elif default_provider == 'sentence_transformers':
                from langchain_huggingface import HuggingFaceEmbeddings
                # Use cache_folder to use locally downloaded models
                cache_folder = os.path.expanduser("~/.cache/huggingface/hub")
                
                # Try to use GPU if available
                device = embed_config.get('device', 'cpu')
                try:
                    import torch
                    if device == 'cuda' and torch.cuda.is_available():
                        print(f"[LLMService] Using GPU for embeddings (CUDA available)")
                    else:
                        device = 'cpu'
                except:
                    device = 'cpu'
                
                return HuggingFaceEmbeddings(
                    model_name=embed_config.get('model', 'all-MiniLM-L6-v2'),
                    cache_folder=cache_folder,
                    model_kwargs={"device": device}
                )
            elif default_provider == 'huggingface':
                from langchain_huggingface import HuggingFaceEmbeddings
                cache_folder = os.path.expanduser("~/.cache/huggingface/hub")
                return HuggingFaceEmbeddings(
                    model_name=embed_config.get('model', 'sentence-transformers/all-mpnet-base-v2'),
                    cache_folder=cache_folder
                )
            elif default_provider == 'ollama':
                # Use Ollama for embeddings (no internet needed)
                from langchain_ollama import OllamaEmbeddings
                return OllamaEmbeddings(
                    model=embed_config.get('model', 'nomic-embed-text'),
                    base_url=embed_config.get('base_url', 'http://localhost:11434')
                )
        except Exception as e:
            print(f"[ERROR] Failed to initialize embeddings with {default_provider}: {e}")
            # Fallback to Ollama if available
            print("[WARNING] Attempting fallback to Ollama embeddings...")
            try:
                from langchain_ollama import OllamaEmbeddings
                return OllamaEmbeddings(model='nomic-embed-text', base_url='http://localhost:11434')
            except:
                # Last resort: use local embeddings without internet
                print("[WARNING] Ollama not available, using fallback embeddings")
                from langchain_huggingface import HuggingFaceEmbeddings
                cache_folder = os.path.expanduser("~/.cache/huggingface/hub")
                return HuggingFaceEmbeddings(
                    model_name='all-MiniLM-L6-v2',
                    cache_folder=cache_folder
                )
    
    def get_model(self) -> BaseChatModel:
        """Get the initialized LLM model"""
        return self.llm
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate text response from prompt
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Generated text response
        """
        response = self.llm.invoke(prompt)
        return response.content
    
    def generate_json(self, prompt: str) -> dict:
        """
        Generate structured JSON response
        
        Args:
            prompt: Input prompt (should request JSON output)
            
        Returns:
            Parsed JSON dictionary
        """
        response = self.llm.invoke(prompt)
        content = response.content
        
        # Extract JSON from markdown code blocks if present
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            print(f"Content: {content}")
            return {}
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for list of texts
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Input text string
            
        Returns:
            Embedding vector
        """
        return self.embeddings.embed_query(text)
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens using tiktoken (cached) or fallback estimation
        
        Args:
            text: Input text
            
        Returns:
            Token count
        """
        if TIKTOKEN_AVAILABLE:
            return self._count_tokens_tiktoken(text)
        else:
            # Fallback: ~4 chars per token average
            return len(text) // 4
    
    @staticmethod
    @lru_cache(maxsize=2048)
    def _count_tokens_tiktoken(text: str) -> int:
        """
        Count tokens using tiktoken with LRU cache
        Cached results for repeated text (typical in RAG systems)
        
        Args:
            text: Input text to tokenize
            
        Returns:
            Token count
        """
        try:
            # Default to cl100k_base encoding (OpenAI models)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            print(f"[WARNING] Tiktoken fallback: {e}")
            return len(text) // 4
    
    def estimate_cost(self, text: str, provider: str = None) -> Dict[str, float]:
        """
        Estimate token cost for text input
        
        Args:
            text: Input text
            provider: LLM provider (uses default if not specified)
            
        Returns:
            Cost breakdown dict with input_cost, output_estimate, total_estimate
        """
        provider = provider or self.provider
        token_count = self.count_tokens(text)
        
        # Pricing per 1M tokens (approximate as of 2024)
        pricing = {
            'openai': {'gpt-4': {'input': 0.03, 'output': 0.06}, 
                       'gpt-4-turbo': {'input': 0.01, 'output': 0.03}},
            'anthropic': {'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
                         'claude-3-opus': {'input': 0.015, 'output': 0.075}},
            'ollama': {'default': {'input': 0.0, 'output': 0.0}},  # Local = free
            'huggingface': {'default': {'input': 0.0, 'output': 0.0}}  # API varies
        }
        
        provider_pricing = pricing.get(provider, {'default': {'input': 0.0, 'output': 0.0}})
        
        # Get model-specific pricing or use default
        model_key = next(iter(provider_pricing.keys())) if provider_pricing else 'default'
        rates = provider_pricing.get(model_key, {'input': 0.0, 'output': 0.0})
        
        input_cost = (token_count / 1_000_000) * rates['input']
        output_estimate = (token_count * 1.5 / 1_000_000) * rates['output']  # Estimate output ~1.5x input
        
        return {
            'input_tokens': token_count,
            'input_cost_usd': round(input_cost, 6),
            'output_estimate_cost_usd': round(output_estimate, 6),
            'total_estimate_usd': round(input_cost + output_estimate, 6),
            'provider': provider
        }
