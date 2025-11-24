"""Ingestion Tools - Optimized document processing and database tracking"""
import json
import sqlite3
import datetime
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..config.env_config import EnvConfig


@tool
def chunk_document_tool(text: str, strategy: str = "recursive", chunk_size: int = 500, overlap: int = 50) -> str:
    """Chunk document using specified strategy"""
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = splitter.split_text(text)
        result = [
            {
                "chunk_id": f"chunk_{i}",
                "text": chunk,
                "strategy": strategy,
                "size": len(chunk),
                "index": i
            }
            for i, chunk in enumerate(chunks)
        ]
        
        return json.dumps({
            "success": True,
            "num_chunks": len(result),
            "chunks": result
        })
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def extract_metadata_tool(text: str, llm_service) -> str:
    """Extract metadata from document using LLM"""
    try:
        prompt = f"""Extract metadata from this document:
        
Document (first 2000 chars):
{text[:2000]}

Return JSON with: title, summary (2-3 sentences), keywords (5-10), topics, doc_type (manual|policy|technical_doc|report|incident)

Example: {{"title": "...", "summary": "...", "keywords": [...], "topics": [...], "doc_type": "..."}}"""
        
        result = llm_service.generate_json(prompt)
        
        # Validate result is proper JSON
        if isinstance(result, dict):
            return json.dumps({"success": True, "metadata": result})
        else:
            # If LLM returned string, try to parse it
            parsed = json.loads(result) if isinstance(result, str) else result
            return json.dumps({"success": True, "metadata": parsed})
        
    except json.JSONDecodeError as e:
        # Return minimal metadata on JSON parse error
        return json.dumps({
            "success": True, 
            "metadata": {
                "title": "Document",
                "summary": text[:200],
                "keywords": ["document"],
                "topics": [],
                "doc_type": "incident"
            }
        })
    except Exception as e:
        # Return minimal metadata on any error
        return json.dumps({
            "success": True,
            "metadata": {
                "title": "Document", 
                "summary": "Unable to extract metadata",
                "keywords": [],
                "topics": [],
                "doc_type": "incident"
            }
        })



@tool
def save_to_vectordb_tool(chunks: str, doc_id: str, llm_service, vectordb_service, 
                         metadata: str = None, rbac_namespace: str = "general",
                         healing_suggestions: str = "") -> str:
    """Save chunks to vector DB with RBAC namespace and healing suggestions"""
    try:
        chunks_data = json.loads(chunks) if isinstance(chunks, str) else chunks
        
        if not chunks_data.get('success'):
            return json.dumps({"success": False, "error": "Invalid chunks data"})
        
        chunk_list = chunks_data.get('chunks', [])
        if not chunk_list:
            return json.dumps({"success": False, "error": "No chunks to save"})
        
        # Parse metadata
        doc_metadata = {}
        if metadata:
            try:
                meta_data = json.loads(metadata) if isinstance(metadata, str) else metadata
                if meta_data.get('success'):
                    doc_metadata = meta_data.get('metadata', {})
                elif isinstance(meta_data, dict):
                    doc_metadata = meta_data
            except:
                pass
        
        # Initialize database connection
        rag_db_path = EnvConfig.get_db_path()
        rag_conn = sqlite3.connect(rag_db_path)
        rag_conn.row_factory = sqlite3.Row
        
        # Import model
        from ...database.models import EmbeddingMetadataModel
        emb_model = EmbeddingMetadataModel(rag_conn)
        
        # Process chunks
        saved_count = 0
        chunk_ids = []
        embeddings = []
        texts = []
        metadatas = []
        
        # Clean metadata
        cleaned_metadata = {}
        for key, value in doc_metadata.items():
            if isinstance(value, (list, dict)):
                cleaned_metadata[key] = json.dumps(value)
            else:
                cleaned_metadata[key] = str(value)
        
        cleaned_metadata['rbac_namespace'] = rbac_namespace
        if healing_suggestions:
            cleaned_metadata['healing_optimized'] = 'true'
        
        for chunk in chunk_list:
            chunk_id = f"{doc_id}_{chunk.get('chunk_id', chunk.get('index', 0))}"
            chunk_text = chunk.get('text', '')
            
            if not chunk_text.strip():
                continue
            
            # Generate embedding
            embedding = llm_service.generate_embedding(chunk_text)
            
            chunk_ids.append(chunk_id)
            embeddings.append(embedding)
            texts.append(chunk_text)
            metadatas.append({
                "doc_id": doc_id,
                "chunk_index": chunk.get('index', 0),
                "rbac_namespace": rbac_namespace,
                **cleaned_metadata
            })
            
            # Store embedding metadata
            try:
                emb_model.insert({
                    'embedding_id': chunk_id,
                    'document_id': doc_id,
                    'chunk_id': chunk_id,
                    'chunk_strategy': chunk.get('strategy', 'recursive'),
                    'chunk_size': chunk.get('size', len(chunk_text)),
                    'overlap': 50,
                    'embedding_model': 'ollama',
                    'embedding_version': '1.0',
                    'quality_score': 0.95,
                    'last_modified': datetime.datetime.now().isoformat(),
                    'reindex_count': 0,
                    'rbac_namespace': rbac_namespace,
                    'metadata_tags': json.dumps(cleaned_metadata),
                    'healing_suggestions': healing_suggestions if healing_suggestions else None
                })
            except Exception as e:
                print(f"[WARNING] Failed to insert metadata for {chunk_id}: {str(e)}")
            
            saved_count += 1
        
        if not chunk_ids:
            rag_conn.close()
            return json.dumps({"success": False, "error": "No valid chunks after processing"})
        
        # Commit embedding metadata changes
        rag_conn.commit()
        
        # Add to vector DB
        vectordb_service.collection.add(
            ids=chunk_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        rag_conn.close()
        
        return json.dumps({
            "success": True,
            "doc_id": doc_id,
            "chunks_saved": saved_count,
            "chunk_ids": chunk_ids,
            "rbac_namespace": rbac_namespace,
            "metadata_updated": True,
            "healing_optimized": bool(healing_suggestions)
        })
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def record_agent_operation_tool(agent_name: str, operation_type: str, status: str,
                               doc_id: str, chunks_count: int) -> str:
    """Record agent operation in database"""
    try:
        rag_db_path = EnvConfig.get_db_path()
        rag_conn = sqlite3.connect(rag_db_path)
        cursor = rag_conn.cursor()
        
        # Insert directly to match actual table schema
        cursor.execute("""
            INSERT INTO agent_operations 
            (agent_id, operation_type, status, input_data, output_data, error_message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            agent_name,
            operation_type,
            status,
            json.dumps({"doc_id": doc_id}),
            json.dumps({"chunks_created": chunks_count}),
            None
        ))
        
        rag_conn.commit()
        rag_conn.close()
        return json.dumps({"success": True})
        
    except Exception as e:
        print(f"[WARNING] Failed to record operation: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def record_agent_memory_tool(agent_name: str, memory_key: str, memory_value: str, 
                            memory_type: str = "context") -> str:
    """Store agent memory for future retrievals"""
    try:
        rag_db_path = EnvConfig.get_db_path()
        rag_conn = sqlite3.connect(rag_db_path)
        
        from ...database.models import AgentMemoryModel
        mem_model = AgentMemoryModel(rag_conn)
        
        mem_model.insert({
            'agent_id': agent_name,
            'memory_type': memory_type,
            'content': memory_value,
            'importance_score': 0.8,
            'created_at': datetime.datetime.now().isoformat()
        })
        
        rag_conn.commit()
        rag_conn.close()
        return json.dumps({"success": True})
        
    except Exception as e:
        print(f"[WARNING] Failed to record memory: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def record_agent_spawn_tool(parent_agent: str, child_agent: str, 
                           task_description: str, status: str = "spawned") -> str:
    """Record agent spawning event"""
    try:
        rag_db_path = EnvConfig.get_db_path()
        rag_conn = sqlite3.connect(rag_db_path)
        
        from ...database.models import BaseModel
        spawn_model = BaseModel(rag_conn)
        spawn_model.table = 'agent_spawns'
        
        spawn_model.insert({
            'parent_agent': parent_agent,
            'child_agent': child_agent,
            'task_description': task_description,
            'status': status,
            'created_at': datetime.datetime.now().isoformat(),
            'completed_at': None
        })
        
        rag_conn.close()
        return json.dumps({"success": True})
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def ingest_sqlite_table_tool(table_name: str, text_columns: list, metadata_columns: list = None,
                            db_path: str = None, llm_service=None, vectordb_service=None,
                            chunk_size: int = 512, chunk_overlap: int = 50,
                            chunk_strategy: str = "per_record", where_clause: str = None) -> str:
    """
    Generic tool to ingest any SQLite table into RAG vector database
    
    Args:
        table_name: Name of SQLite table to ingest (e.g., "knowledge_base", "incidents", "policies")
        text_columns: List of column names to combine as searchable text
        metadata_columns: List of column names to attach as metadata (optional)
        db_path: Path to SQLite database (uses config if None)
        llm_service: LLM service for embeddings
        vectordb_service: Vector DB service (Chroma)
        chunk_size: Semantic chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens
        chunk_strategy: "per_record" (one document per row) or "sequential" (combine rows)
        where_clause: Optional SQL WHERE clause for filtering records (e.g., "environment = 'prod'")
    
    Returns:
        JSON with ingestion status and statistics
        
    Example:
        result = ingest_sqlite_table_tool(
            table_name="policies",
            text_columns=["policy_title", "policy_content", "guidelines"],
            metadata_columns=["policy_id", "category", "department", "effective_date"],
            chunk_strategy="per_record",
            where_clause="status = 'active'"
        )
    """
    try:
        # Use config database path if not provided
        if db_path is None:
            db_path = EnvConfig.get_db_path()
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Validate table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return json.dumps({
                "success": False,
                "error": f"Table '{table_name}' does not exist in database"
            })
        
        # Build query
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        # Fetch all records
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return json.dumps({
                "success": False,
                "error": f"No records found in table '{table_name}'"
            })
        
        # Process records based on chunk strategy
        documents = []
        
        if chunk_strategy == "per_record":
            # One document per database record
            for row in rows:
                row_dict = dict(row)
                
                # Combine text columns into document content
                text_parts = []
                for col in text_columns:
                    if col in row_dict and row_dict[col]:
                        value = row_dict[col]
                        text_parts.append(f"{col}: {value}")
                
                document_text = "\n".join(text_parts)
                
                if document_text.strip():
                    # Extract metadata
                    metadata = {}
                    if metadata_columns:
                        for col in metadata_columns:
                            if col in row_dict:
                                metadata[col] = row_dict[col]
                    
                    documents.append({
                        "text": document_text,
                        "metadata": metadata,
                        "table": table_name
                    })
        
        elif chunk_strategy == "sequential":
            # Combine records sequentially (multiple records per document)
            combined_text_parts = []
            combined_metadata = {"record_count": 0}
            
            for row in rows:
                row_dict = dict(row)
                text_parts = []
                
                for col in text_columns:
                    if col in row_dict and row_dict[col]:
                        value = row_dict[col]
                        text_parts.append(f"{col}: {value}")
                
                document_section = "\n".join(text_parts)
                if document_section.strip():
                    combined_text_parts.append(f"--- Record ---\n{document_section}")
                    combined_metadata["record_count"] += 1
            
            if combined_text_parts:
                documents.append({
                    "text": "\n\n".join(combined_text_parts),
                    "metadata": combined_metadata,
                    "table": table_name
                })
        
        else:
            conn.close()
            return json.dumps({
                "success": False,
                "error": f"Unknown chunk_strategy: {chunk_strategy}. Use 'per_record' or 'sequential'"
            })
        
        if not documents:
            return json.dumps({
                "success": False,
                "error": "No documents created after processing records"
            })
        
        # Chunk each document semantically
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        ingestion_results = {
            "table_name": table_name,
            "records_processed": len(rows),
            "documents_created": len(documents),
            "chunks": []
        }
        
        # Process each document
        chunk_counter = 0
        for doc_idx, doc in enumerate(documents):
            # Chunk the document
            chunks = splitter.split_text(doc["text"])
            
            for chunk_idx, chunk_text in enumerate(chunks):
                if not chunk_text.strip():
                    continue
                
                # Generate chunk ID
                chunk_id = f"{table_name}_doc_{doc_idx}_chunk_{chunk_idx}_{int(datetime.datetime.now().timestamp() * 1000)}"
                
                # Generate embedding
                embedding = llm_service.generate_embedding(chunk_text)
                
                # Prepare chunk metadata
                chunk_metadata = {
                    "table": table_name,
                    "document_index": doc_idx,
                    "chunk_index": chunk_idx,
                    "chunk_strategy": chunk_strategy,
                    "source_records": len(rows) if chunk_strategy == "sequential" else 1,
                    **doc["metadata"]
                }
                
                # Save to vector DB
                vectordb_service.collection.add(
                    ids=[chunk_id],
                    documents=[chunk_text],
                    embeddings=[embedding],
                    metadatas=[chunk_metadata]
                )
                
                ingestion_results["chunks"].append({
                    "chunk_id": chunk_id,
                    "chunk_size": len(chunk_text),
                    "metadata": chunk_metadata
                })
                
                chunk_counter += 1
        
        ingestion_results["total_chunks_created"] = chunk_counter
        
        return json.dumps({
            "success": True,
            **ingestion_results
        })
        
    except Exception as e:
        import traceback
        return json.dumps({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
