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
