"""
RAG Master Orchestrator - Clean deepagents implementation with SubAgentMiddleware
"""
import json
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain_core.tools import tool
from langchain.agents.middleware import AgentMiddleware

# Import subagent classes
from .ingestion_subagent import IngestionSubAgent
from .retrieval_subagent import RetrievalSubAgent

# Global reference to the master agent instance
_rag_master_agent_instance = None

def set_rag_master_agent_instance(agent_instance):
    global _rag_master_agent_instance
    _rag_master_agent_instance = agent_instance

@tool
def ingest_document(document_path: str) -> str:
    """Ingest a document from a file path."""
    if _rag_master_agent_instance is None:
        return "Error: Master agent instance not set."
    return _rag_master_agent_instance.ingestion_subagent.execute({'data': document_path})

@tool
def retrieve_info(query: str) -> str:
    """Retrieve information from the vector database."""
    if _rag_master_agent_instance is None:
        return "Error: Master agent instance not set."
    return _rag_master_agent_instance.retrieval_subagent.execute({'query': query})

class RAGToolMiddleware(AgentMiddleware):
    tools = [ingest_document, retrieve_info]

class RAGMasterAgent:
    """Clean RAG Master Orchestrator using deepagents SubAgentMiddleware."""
    
    def __init__(self, services: Optional[Dict[str, Any]] = None, config: Optional[Dict] = None):
        """Initialize master orchestrator with automatic service setup or provided services."""
        self.config = config or {'verbose': True}
        self.name = "RAGMasterAgent"
        
        # Configure verbose logging FIRST (needed for service initialization)
        self.verbose = self.config.get('verbose', True)
        
        # Initialize services automatically if not provided
        if services is None:
            services = self._initialize_services()
        
        self.services = services
        self.llm_service = services.get("llm")
        self.vectordb_service = services.get("vectordb") 
        
        # Initialize metrics
        self.metrics = {"operations": 0, "ingestion": 0, "retrieval": 0, "errors": 0}
        
        # Initialize subagent instances
        self.ingestion_subagent = IngestionSubAgent(services, parent=self)
        self.retrieval_subagent = RetrievalSubAgent(services, parent=self)
        
        # Setup agent with subagent middleware
        set_rag_master_agent_instance(self)
        self._create_agent()
    
    def _initialize_services(self) -> Dict[str, Any]:
        """Initialize real services automatically."""
        try:
            from langchain_ollama import ChatOllama, OllamaEmbeddings
            import chromadb
            
            # Real Ollama LLM with optimized settings to prevent crashes
            class SimpleLLMService:
                def __init__(self):
                    self.llm = ChatOllama(
                        model="qwen2.5:0.5b",
                        base_url="http://localhost:11434",
                        temperature=0,
                        num_ctx=2048,  # Reduced context window to prevent OOM
                        num_predict=512,  # Limit output tokens
                        repeat_penalty=1.1
                    )
                    self._embeddings = OllamaEmbeddings(
                        model="nomic-embed-text",
                        base_url="http://localhost:11434"
                    )
                    
                def generate_embedding(self, text: str):
                    return self._embeddings.embed_query(text)
                
                def generate_response(self, prompt: str) -> str:
                    response = self.llm.invoke(prompt)
                    return response.content
            
            # Real ChromaDB
            class SimpleVectorDBService:
                def __init__(self):
                    self.client = chromadb.PersistentClient(path="src/incident_iq/database/data/chroma_db")
                    try:
                        self.collection = self.client.get_collection("documents")
                    except:
                        self.collection = self.client.create_collection("documents")
                
                def search(self, query, top_k=5):
                    # Simple search implementation
                    results = self.collection.query(query_texts=[query], n_results=top_k)
                    return results
            
            llm_service = SimpleLLMService()
            vectordb_service = SimpleVectorDBService()
            
            if self.verbose:
                print("✅ [INIT] Real services initialized automatically")
                
            return {"llm": llm_service, "vectordb": vectordb_service}
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize services: {str(e)}. Ensure Ollama is running.")
    
    def _create_agent(self) -> None:
        """Create deepagents agent with proper middleware configuration."""
        
        print("🔧 [SETUP] Initializing RAG Master Agent with custom middleware.")
        
        # Import langchain tools for subagents
        from ..tools.ingestion_tools import (
            chunk_document_tool,
            extract_metadata_tool, 
            save_to_vectordb_tool,
            ingest_sqlite_table_tool
        )
        
        # Define subagents. The SubAgentMiddleware will turn these into tools for the master agent.
        subagents = [
            {
                "name": "ingestion_specialist",
                "description": "Use this specialist for any and all tasks related to ingesting, processing, and storing documents from a file path.",
                "system_prompt": "You are a document ingestion specialist. Your job is to use the available tools to process and store documents.",
                "tools": [chunk_document_tool, extract_metadata_tool, save_to_vectordb_tool, ingest_sqlite_table_tool],
                "model": self.llm_service.llm,
            },
            {
                "name": "retrieval_specialist", 
                "description": "Use this specialist for any and all tasks related to searching, querying, and retrieving information from stored documents.",
                "system_prompt": "You are a document retrieval specialist. Your job is to find and synthesize answers from the vector database.",
                "tools": [], # This subagent will use its internal services for retrieval
                "model": self.llm_service.llm,
            }
        ]
        
        print("📋 [SETUP] Using deepagents auto-middleware with subagents parameter.")
        
        # Let deepagents handle all middleware automatically by passing the subagents list.
        # The master agent will have NO tools of its own; its tools ARE the subagents.
        self.agent = create_deep_agent(
            model=self.llm_service.llm,
            system_prompt=self._get_system_prompt(),
            middleware=[RAGToolMiddleware()]
        )
        
        print("✅ [SETUP] RAG Master Agent initialized with custom middleware.")
    
    def _get_system_prompt(self) -> str:
        """A simple, direct system prompt that instructs the agent to use its subagent tools."""
        return """You are a master orchestrator. Your ONLY job is to delegate tasks to one of your specialized subagents. You MUST follow these rules.

AVAILABLE SUBAGENT TOOLS:
- `ingestion_specialist`: Call this subagent for ANY request related to adding, processing, storing, or ingesting documents. The entire user request should be passed as input.
- `retrieval_specialist`: Call this subagent for ANY request related to searching, finding, querying, or retrieving information. The entire user request should be passed as input.

DELEGATION RULES (MANDATORY):
1.  If the user's request contains keywords like "ingest", "process document", "add file", "store data", or a file path, you MUST delegate the entire request to the `ingestion_specialist`.
2.  If the user's request contains keywords like "search", "find", "query", "what is", or asks a question, you MUST delegate the entire request to the `retrieval_specialist`.
3.  You do not have the ability to answer questions or process files directly. You MUST delegate to a subagent.

Example 1:
User Request: "Please ingest the document at test_documents/report.txt"
Your Action: Call the `ingestion_specialist` tool with the input "Please ingest the document at test_documents/report.txt".

Example 2:
User Request: "What happened during the network outage?"
Your Action: Call the `retrieval_specialist` tool with the input "What happened during the network outage?".
"""
    
    # ========================================================================
    # PUBLIC API 
    # ========================================================================
    
    def process_request(self, request: str) -> str:
        """Main entry point with TodoList tracking and verbose logging."""
        start_time = time.time()
        
        print(f"\n🎯 [MASTER] Processing request: {request[:100]}...")
        print(f"⏱️  [MASTER] Started at: {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            # Enhanced request with explicit TodoList instructions
            enhanced_request = request # No more complex prompt wrapping
            
            # Invoke with middleware handling all the routing and logging
            response = self.agent.invoke({"input": request})
            
            # Update metrics  
            self.metrics["operations"] += 1
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            print(f"⏱️  [MASTER] Completed in: {elapsed_ms}ms")
            print(f"📊 [MASTER] Total operations: {self.metrics['operations']}")
            
            # Extract response content
            content = getattr(response, 'content', str(response))
            result = content.strip()
            
            print(f"✅ [MASTER] Request completed successfully")
            return result
            
        except Exception as e:
            self.metrics["errors"] += 1
            error_msg = f"Request failed: {str(e)}"
            print(f"❌ [MASTER] {error_msg}")
            return error_msg
    
    def ingest_document(self, document_path: str) -> str:
        """Simple document ingestion."""
        request = f"Please ingest the document at: {document_path}"
        result = self.process_request(request)
        self.metrics["ingestion"] += 1
        return result
    
    def ask_question(self, question: str) -> str:
        """Simple question answering."""
        request = f"Please search for information to answer: {question}"
        result = self.process_request(request)
        self.metrics["retrieval"] += 1
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get operational metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset metrics."""
        self.metrics = {"operations": 0, "ingestion": 0, "retrieval": 0, "errors": 0}
    
    def receive_subagent_result(self, subagent_name: str, result: Dict[str, Any]) -> None:
        """Receive and process results from subagents."""
        if self.verbose:
            success = result.get('success', False)
            status = "✅" if success else "❌"
            print(f"{status} [SUBAGENT] {subagent_name} completed: {result.get('error', 'Success')}")
    
    def debug_workflow(self, request: str) -> str:
        """Debug version that shows internal deepagents workflow."""
        print(f"\n🔍 [DEBUG] Starting deepagents workflow visualization...")
        print(f"📝 [DEBUG] Request: {request[:80]}...")
        
        try:
            # Step 1: Show initial TodoList state
            print(f"\n📋 [DEBUG] Checking initial TodoList...")
            todo_response = self.agent.invoke({"input": "Use read_todos to show current status"})
            todo_content = getattr(todo_response, 'content', str(todo_response))
            print(f"📋 [INITIAL TODOS] {todo_content[:200]}...")
            
            # Step 2: Process the main request with verbose logging
            print(f"\n🎯 [DEBUG] Processing main request with full tracking...")
            enhanced_request = f"""PROCESS WITH MAXIMUM VISIBILITY:
            
Request: {request}

WORKFLOW REQUIREMENTS:
1. Use write_todos to add: 'Starting request: {request[:30]}...'
2. Analyze what type of request this is
3. Use write_todos to add: 'Request type identified: [type]'
4. Choose and delegate to appropriate subagent
5. Use write_todos to add: 'Delegating to [subagent] subagent'
6. Monitor subagent progress
7. Use write_todos to add: 'Subagent completed with result'
8. Use read_todos to show final status
9. Provide detailed summary

BE EXTREMELY VERBOSE about EVERY step and TodoList interaction."""
            
            response = self.agent.invoke({"input": enhanced_request})
            
            # Step 3: Show final TodoList state
            print(f"\n📋 [DEBUG] Checking final TodoList state...")
            final_todo_response = self.agent.invoke({"input": "Use read_todos to show all completed and pending tasks"})
            final_todo_content = getattr(final_todo_response, 'content', str(final_todo_response))
            print(f"📋 [FINAL TODOS] {final_todo_content[:300]}...")
            
            # Extract and return main response
            content = getattr(response, 'content', str(response))
            print(f"\n✅ [DEBUG] Workflow visualization complete")
            return content
            
        except Exception as e:
            error_msg = f"Debug workflow failed: {str(e)}"
            print(f"❌ [DEBUG] {error_msg}")
            return error_msg

