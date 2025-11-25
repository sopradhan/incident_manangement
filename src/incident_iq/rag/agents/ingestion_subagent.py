"""
Ingestion SubAgent for RAG Master Agent
Specialized for document processing and storage operations
"""
import json
import time
from pathlib import Path
from typing import Union, List, Dict, Any, Optional
from datetime import datetime

from ..config.env_config import EnvConfig
from ..tools.ingestion_tools import (
    chunk_document_tool,
    extract_metadata_tool,
    save_to_vectordb_tool,
)
from ..tools.markdown_converter import (
    file_to_markdown,
    sqlite_table_to_markdown,
)

# Domain constants
VALID_DOMAINS = ["finance", "medical", "legal", "technical", "travel", "general"]
DOMAIN_NAMESPACE_MAP = {
    "finance": "finance",
    "medical": "healthcare", 
    "legal": "legal",
    "travel": "operations",
    "technical": "engineering",
    "general": "general",
}


class IngestionSubAgent:
    """
    SubAgent specialized for document ingestion operations.
    
    Handles:
    - Document processing in multiple formats
    - Domain detection and classification
    - Semantic chunking with configurable strategies
    - Metadata extraction and quality validation
    - Embedding generation and vector storage
    """
    
    def __init__(self, services: Dict[str, Any], parent=None):
        """
        Initialize ingestion subagent.
        
        Args:
            services: Dictionary containing 'llm' and 'vectordb' service instances
            parent: Reference to parent RAGMasterAgent (optional)
        """
        self.services = services
        self.parent = parent
        self.name = "IngestionSubAgent"
        self.llm_service = services.get("llm")
        self.vectordb_service = services.get("vectordb")
        
        # Configuration
        self.chunk_size = 500
        self.chunk_overlap = 50
        self.chunking_strategy = "recursive"
        
        # Initialize metrics
        self.metrics = {
            "documents_processed": 0,
            "chunks_created": 0,
            "processing_time_ms": 0
        }
    

    
    # ========================================================================
    # PUBLIC API METHODS
    # ========================================================================
    
    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ingestion operation based on request.
        
        Args:
            request: Dictionary with ingestion details:
                {
                    'data': <data_to_process>,
                    'metadata': <optional_metadata>,
                    'domain': <optional_domain>,
                    'config': <optional_config_overrides>
                }
        
        Returns:
            Dictionary with ingestion results
        """
        start_time = time.time()
        
        try:
            # Extract data from request
            data = request.get('data')
            metadata = request.get('metadata')
            domain = request.get('domain')
            config = request.get('config', {})
            
            if not data:
                raise ValueError("No data provided for ingestion")
            
            # Apply config overrides
            self._apply_config(config)
            
            # Execute ingestion
            result = self._ingest_data(data, metadata, domain)
            
            # Update metrics
            elapsed_ms = int((time.time() - start_time) * 1000)
            self._update_metrics(result, elapsed_ms)
            
            # Notify parent if available
            if self.parent:
                self.parent.receive_subagent_result('ingestion', result)
            
            return result
            
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            error_result = {
                "success": False,
                "error": str(e),
                "time_ms": elapsed_ms
            }
            
            if self.parent:
                self.parent.receive_subagent_result('ingestion', error_result)
                
            return error_result
    
    def ingest_data(self, data: Union[str, List, Dict], metadata: Optional[Dict] = None, 
                   domain: Optional[str] = None) -> Dict[str, Any]:
        """Direct ingestion method (backward compatibility)."""
        request = {
            'data': data,
            'metadata': metadata,
            'domain': domain
        }
        return self.execute(request)
    
    # ========================================================================
    # PRIVATE HELPER METHODS  
    # ========================================================================
    
    def _apply_config(self, config: Dict[str, Any]) -> None:
        """Apply configuration overrides."""
        self.chunk_size = config.get('chunk_size', self.chunk_size)
        self.chunk_overlap = config.get('chunk_overlap', self.chunk_overlap)
        self.chunking_strategy = config.get('chunking_strategy', self.chunking_strategy)
    
    def _ingest_data(self, data: Union[str, List, Dict], metadata: Optional[Dict], 
                    domain: Optional[str]) -> Dict[str, Any]:
        """Core ingestion logic."""
        # Step 1: Normalize input
        documents = self._normalize_input(data)
        if not documents:
            return self._error_result("No valid documents after normalization")
        
        # Step 2: Detect domain if not provided
        if domain is None:
            domain = self._detect_domain(documents)
        domain = domain.lower() if domain in VALID_DOMAINS else "general"
        
        # Step 3: Extract metadata if not provided
        if metadata is None:
            metadata = self._extract_metadata(documents, domain)
        
        # Step 4: Process documents
        doc_ids = []
        total_chunks = 0
        
        for i, doc in enumerate(documents):
            result = self._process_single_document(doc, i, domain)
            
            if result.get("success"):
                doc_ids.append(result.get("doc_id"))
                total_chunks += result.get("chunks_created", 0)
            else:
                print(f"[WARN] Document {i} failed: {result.get('error')}")
        
        return {
            "success": len(doc_ids) > 0,
            "documents_ingested": len(doc_ids),
            "doc_ids": doc_ids,
            "domain": domain,
            "metadata": metadata,
            "chunks_created": total_chunks
        }
    
    def _normalize_input(self, data: Union[str, List, Dict]) -> List[str]:
        """Normalize input to list of document strings."""
        documents = []
        
        if isinstance(data, str):
            path = Path(data)
            if path.exists():
                # File path - convert using markdown converter
                try:
                    result = json.loads(file_to_markdown(str(path)))
                    if result.get("success"):
                        documents.append(result.get("markdown", ""))
                    else:
                        documents.append(path.read_text())
                except Exception as e:
                    print(f"[WARN] Failed to process file {data}: {e}")
                    documents.append(str(data))
            else:
                # Plain text string
                documents.append(data)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    documents.append(item)
                else:
                    documents.append(str(item))
        
        elif isinstance(data, dict):
            # Check if this is a SQLite table specification
            if "sqlite_db_path" in data and "table_name" in data:
                try:
                    # Convert SQLite table to markdown
                    result = json.loads(sqlite_table_to_markdown(
                        data["sqlite_db_path"], 
                        data["table_name"],
                        data.get("text_columns", [])
                    ))
                    if result.get("success"):
                        documents.append(result.get("markdown", ""))
                    else:
                        print(f"[WARN] Failed to process SQLite table: {result.get('error')}")
                        documents.append(json.dumps(data, indent=2))
                except Exception as e:
                    print(f"[WARN] Failed to process SQLite table {data}: {e}")
                    documents.append(json.dumps(data, indent=2))
            else:
                # Regular dict - convert to JSON
                documents.append(json.dumps(data, indent=2))
        
        else:
            documents.append(str(data))
        
        return [doc for doc in documents if doc.strip()]
    
    def _detect_domain(self, documents: List[str]) -> str:
        """Detect document domain using LLM."""
        sample_text = " ".join(documents[:2])[:500]
        
        try:
            prompt = f"""Classify the following text into one of these domains:
finance, medical, legal, technical, travel, general

Text sample:
{sample_text}

Respond with ONLY the domain name."""
            
            response = self.llm_service.generate_response(prompt).strip().lower()
            return response if response in VALID_DOMAINS else "general"
        except Exception as e:
            print(f"[WARN] Domain detection failed: {e}")
            return "general"
    
    def _extract_metadata(self, documents: List[str], domain: str) -> Dict[str, Any]:
        """Extract metadata from documents."""
        combined_text = " ".join(documents)
        
        return {
            "document_count": len(documents),
            "total_characters": len(combined_text),
            "domain": domain,
            "rbac_namespace": DOMAIN_NAMESPACE_MAP.get(domain, "general"),
            "has_urls": "http://" in combined_text or "https://" in combined_text,
            "has_emails": "@" in combined_text,
            "ingestion_timestamp": datetime.now().isoformat(),
        }
    
    def _process_single_document(self, doc: str, doc_index: int, domain: str) -> Dict[str, Any]:
        """Process a single document through the ingestion pipeline."""
        doc_id = f"{domain}_doc_{doc_index}_{int(time.time() * 1000)}"
        
        try:
            # Step 1: Chunk document
            chunks_result = chunk_document_tool.invoke({
                "text": doc,
                "strategy": self.chunking_strategy,
                "chunk_size": self.chunk_size,
                "overlap": self.chunk_overlap
            })
            chunks_data = json.loads(chunks_result)
            
            if not chunks_data.get("success"):
                return {
                    "success": False,
                    "doc_id": doc_id,
                    "error": chunks_data.get("error", "Chunking failed")
                }
            
            # Step 2: Extract metadata
            metadata_result = extract_metadata_tool.invoke({
                "text": doc,
                "llm_service": self.llm_service
            })
            
            # Step 3: Save to vector database
            save_result = save_to_vectordb_tool.invoke({
                "chunks": chunks_result,
                "doc_id": doc_id,
                "llm_service": self.llm_service,
                "vectordb_service": self.vectordb_service,
                "metadata": metadata_result,
                "rbac_namespace": DOMAIN_NAMESPACE_MAP.get(domain, "general")
            })
            save_data = json.loads(save_result)
            
            if not save_data.get("success"):
                return {
                    "success": False,
                    "doc_id": doc_id,
                    "error": save_data.get("error", "Failed to save to vector DB")
                }
            
            return {
                "success": True,
                "doc_id": doc_id,
                "chunks_created": chunks_data.get("num_chunks", 0),
                "chunks_saved": save_data.get("chunks_saved", 0)
            }
            
        except Exception as e:
            return {"success": False, "doc_id": doc_id, "error": str(e)}
    
    def _update_metrics(self, result: Dict[str, Any], elapsed_ms: int) -> None:
        """Update ingestion metrics."""
        if result.get("success"):
            self.metrics["documents_processed"] += result.get("documents_ingested", 0)
            self.metrics["chunks_created"] += result.get("chunks_created", 0)
        self.metrics["processing_time_ms"] += elapsed_ms
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result dictionary."""
        return {
            "success": False,
            "error": error_message,
            "documents_ingested": 0,
            "doc_ids": [],
            "chunks_created": 0
        }
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get subagent metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset subagent metrics."""
        self.metrics = {
            "documents_processed": 0,
            "chunks_created": 0,
            "processing_time_ms": 0
        }