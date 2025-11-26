"""Ingestion Tools - Optimized document processing and database tracking"""
import json
import sqlite3
import datetime
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..config.env_config import EnvConfig

@tool
def extract_metadata_tool(text: str, llm_service) -> str:
    """
    Extracts high-level metadata from the document using the LLM's structured output capability.
    
    Args:
        text (str): The full or truncated document text for analysis.
        llm_service: Service object providing a .generate_json(prompt) method.

    Returns:
        JSON string with 'success' and the extracted 'metadata' dictionary.
    """
    try:
        prompt = f"""Extract metadata from this document:
        
Document (first 2000 chars):
{text[:2000]}

Return JSON with: title, summary (2-3 sentences), keywords (5-10 list), topics (list), doc_type (manual|policy|technical_doc|report|incident|table_ingest).

Example: {{"title": "...", "summary": "...", "keywords": [...], "topics": [...], "doc_type": "..."}}"""
        
        result = llm_service.generate_json(prompt)
        parsed = result if isinstance(result, dict) else json.loads(result)
        
        return json.dumps({"success": True, "metadata": parsed})
        
    except Exception as e:
        # Robust fallback on any failure
        fallback_metadata = {
            "title": "Document",
            "summary": "Unable to extract detailed metadata.",
            "keywords": ["document", "metadata_failure"],
            "topics": ["unknown"],
            "doc_type": "report"
        }
        return json.dumps({"success": True, "metadata": fallback_metadata})


@tool
def chunk_document_tool(text: str, doc_id: str, strategy: str = "recursive", 
                        chunk_size: int = 500, overlap: int = 50) -> str:
    """
    Splits text (often Markdown-formatted) into smaller chunks using a recursive strategy.
    
    Args:
        text (str): The document content to be chunked.
        doc_id (str): The unique ID of the source document/file.
        strategy (str): The splitting strategy (only 'recursive' implemented).
        chunk_size (int): Max number of characters per chunk.
        overlap (int): Overlap between chunks.

    Returns:
        JSON string with 'success', 'num_chunks', and a list of 'chunks'.
    """
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            # Optimized separators for Markdown/general text structure
            separators=["\n\n##", "\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = splitter.split_text(text)
        result = [
            {
                "chunk_id": f"{doc_id}_chunk_{i}",
                "text": chunk,
                "strategy": strategy,
                "size": len(chunk),
                "index": i
            }
            for i, chunk in enumerate(chunks)
        ]
        
        return json.dumps({
            "success": True,
            "doc_id": doc_id,
            "num_chunks": len(result),
            "chunks": result
        })
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
#############

@tool
def save_to_vectordb_tool(chunks: str, doc_id: str, llm_service, vectordb_service, 
                          metadata: str = None, rbac_namespace: str = "general") -> str:
    """
    Generates embeddings for a list of chunks and saves them to:
    1. Vector DB (ChromaDB) - for similarity search
    2. SQLite (optimized schema) - for metadata tracking

    Args:
        chunks (str): JSON string returned by chunk_document_tool.
        doc_id (str): Unique ID for the source document/file.
        llm_service: Service object for .generate_embedding(text).
        vectordb_service: Service object for VDB .collection.add(...).
        metadata (str): JSON string of document-level metadata.
        rbac_namespace (str): Namespace/Collection name for RBAC filtering.

    Returns:
        JSON with 'success', 'doc_id', 'chunks_saved', and VDB details.
    """
    try:
        chunks_data = json.loads(chunks) if isinstance(chunks, str) else chunks
        chunk_list = chunks_data.get('chunks', [])
        
        if not chunks_data.get('success') or not chunk_list:
             return json.dumps({"success": False, "error": "Invalid or empty chunks list provided."})
        
        # 1. Parse Metadata
        doc_metadata = {}
        if metadata:
            meta_data = json.loads(metadata) if isinstance(metadata, str) else {}
            doc_metadata = meta_data.get('metadata', {})

        # 2. Prepare Data Structures
        chunk_ids = []
        embeddings = []
        texts = []
        metadatas = []
        
        # Finalize and clean document-level metadata
        cleaned_doc_metadata = {
            "doc_id": doc_id,
            "rbac_namespace": rbac_namespace,
            "ingestion_date": datetime.datetime.now().isoformat(),
            # Flatten/clean LLM-extracted metadata
            **{k: (json.dumps(v) if isinstance(v, (list, dict)) else str(v)) 
               for k, v in doc_metadata.items()}
        }
        
        # 3. Process Chunks (Generate Embeddings & Append)
        for chunk in chunk_list:
            chunk_text = chunk.get('text', '').strip()
            if not chunk_text:
                continue
            
            chunk_id = f"{doc_id}_chunk_{chunk.get('index', 0)}" # Use simpler ID structure
            embedding = llm_service.generate_embedding(chunk_text)
            
            chunk_ids.append(chunk_id)
            embeddings.append(embedding)
            texts.append(chunk_text)
            
            # Combine doc metadata with chunk-specific metadata
            metadatas.append({
                "chunk_index": chunk.get('index', 0),
                **cleaned_doc_metadata
            })
        
        if not chunk_ids:
            return json.dumps({"success": False, "error": "No valid chunk text found after processing."})
        
        # 4. Add to Vector DB (ChromaDB)
        vectordb_service.collection.add(
            ids=chunk_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        # 5. Save to SQLite optimized schema
        try:
            from ...database.models.document_metadata_model import DocumentMetadataModel
            from ...database.models.chunk_embedding_data_model import ChunkEmbeddingDataModel
            
            db_path = EnvConfig.get_db_path()
            print(f"[DEBUG] SQLite save starting: db_path={db_path}")
            
            # Save document metadata
            print(f"[DEBUG] Creating DocumentMetadataModel with doc_id={doc_id}")
            doc_model = DocumentMetadataModel(db_path)
            doc_result = doc_model.create(
                doc_id=doc_id,
                title=doc_metadata.get('title', f'Document {doc_id}'),
                author=doc_metadata.get('author', 'Unknown'),
                source=doc_metadata.get('source', 'ingestion_tool'),
                summary=doc_metadata.get('summary', ''),
                rbac_namespace=rbac_namespace,
                chunk_strategy="recursive_splitter",
                chunk_size_char=500,
                overlap_char=50,
                metadata_json=json.dumps(doc_metadata)
            )
            print(f"[DEBUG] DocumentMetadata created: {doc_result}")
            
            # Save chunk embedding data
            print(f"[DEBUG] Creating ChunkEmbeddingDataModel for {len(chunk_ids)} chunks")
            chunk_model = ChunkEmbeddingDataModel(db_path)
            for i, chunk_id in enumerate(chunk_ids):
                chunk_result = chunk_model.create(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    embedding_model=llm_service.provider if hasattr(llm_service, 'provider') else 'ollama',
                    embedding_version="1.0",
                    quality_score=0.8,  # Default quality score
                    reindex_count=0,
                    healing_suggestions=json.dumps({})
                )
                print(f"[DEBUG] Chunk {i}/{len(chunk_ids)} created: {chunk_result}")
            
            doc_model.close()
            chunk_model.close()
            print(f"[DEBUG] SQLite save completed successfully for {len(chunk_ids)} chunks")
            
        except Exception as e:
            # Log but don't fail if SQLite write fails
            import traceback
            print(f"[ERROR] SQLite metadata save failed: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        return json.dumps({
            "success": True,
            "doc_id": doc_id,
            "chunks_saved": len(chunk_ids),
            "rbac_namespace": rbac_namespace,
        })
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
    
@tool
def update_metadata_tracking_tool(doc_id: str, source_path: str, rbac_namespace: str, 
                                 metadata: str, chunks_saved: int, is_table: bool = False) -> str:
    """
    Updates the central SQLite metadata table (DocumentTrackingModel) with the status 
    of a completed ingestion, including RBAC details.
    
    Args:
        doc_id (str): Unique identifier for the document or table.
        source_path (str): Original file path or DB/table reference.
        rbac_namespace (str): The domain/namespace used for VDB.
        metadata (str): JSON string of document-level metadata.
        chunks_saved (int): Number of embeddings successfully stored.
        is_table (bool): True if the source was a database table.

    Returns:
        JSON with 'success' status.
    """
    try:
        rag_db_path = EnvConfig.get_db_path()
        rag_conn = sqlite3.connect(rag_db_path)
        
        # Assuming DocumentTrackingModel is the correct model for high-level tracking
        from ...database.models import DocumentTrackingModel 
        doc_model = DocumentTrackingModel(rag_conn)
        
        doc_metadata_dict = json.loads(metadata) if isinstance(metadata, str) else {}
        
        doc_model.insert({
            'document_id': doc_id,
            'source_path': source_path,
            'rbac_namespace': rbac_namespace,
            'doc_type': doc_metadata_dict.get('doc_type', 'unknown'),
            'chunks_saved': chunks_saved,
            'is_table': 1 if is_table else 0,
            'ingestion_date': datetime.datetime.now().isoformat(),
            'ingestion_status': 'COMPLETED',
            'metadata_tags': json.dumps(doc_metadata_dict)
        })
        
        rag_conn.commit()
        rag_conn.close()
        
        return json.dumps({"success": True})
        
    except Exception as e:
        return json.dumps({"success": False, "error": f"Metadata tracking failed: {str(e)}"})
    
@tool
def ingest_sqlite_table_tool(table_name: str, doc_id: str, rbac_namespace: str,
                             text_columns: list, metadata_columns: list = None,
                             db_path: str = None, llm_service=None, vectordb_service=None,
                             chunk_size: int = 512, chunk_overlap: int = 50,
                             where_clause: str = None) -> str:
    """
    COMPLETE PIPELINE: Ingests a single SQLite table into the RAG vector database. 
    Converts rows to structured text, chunks, embeds, and stores them in VDB.
    
    Args:
        table_name (str): Name of SQLite table to ingest.
        doc_id (str): Unique ingestion ID (used as the overall document ID).
        rbac_namespace (str): Domain/namespace for RBAC filtering.
        text_columns (list): List of column names to combine as searchable text.
        metadata_columns (list): List of column names to attach as metadata (optional).
        db_path (str): Path to SQLite database (uses config if None).
        llm_service: LLM service for embeddings.
        vectordb_service: Vector DB service.
        chunk_size (int): Max chunk size in characters/tokens.
        chunk_overlap (int): Overlap between chunks.
        where_clause (str): Optional SQL WHERE clause for filtering records.
    
    Returns:
        JSON with ingestion status and statistics.
    """
    try:
        # 1. Setup & Fetch Records
        db_path = db_path if db_path is not None else EnvConfig.get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return json.dumps({"success": False, "error": f"No records found in table '{table_name}'"})
        
        # 2. Process Records (Convert to Structured Documents)
        documents_to_chunk = []
        for row_idx, row in enumerate(rows):
            row_dict = dict(row)
            
            # Create a structured Markdown-like text for high-quality embedding
            text_parts = [f"--- Table Record: {table_name} (Index: {row_idx}) ---"]
            for col in text_columns:
                value = row_dict.get(col)
                if value is not None:
                    text_parts.append(f"**{col.replace('_', ' ').title()}:** {value}")
            
            document_text = "\n".join(text_parts)
            
            # Extract metadata from specified columns
            metadata = {
                "source_table": table_name,
                "rbac_namespace": rbac_namespace,
                "doc_type": "table_record",
                "source_record_index": row_idx # Useful for linking back to SQL row
            }
            if metadata_columns:
                for col in metadata_columns:
                    if col in row_dict:
                        metadata[col] = row_dict[col]

            documents_to_chunk.append({"text": document_text, "metadata": metadata})

        # 3. Chunking, Embedding, and Storing
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        all_chunk_ids, all_texts, all_embeddings, all_metadatas = [], [], [], []
        
        for doc_idx, doc in enumerate(documents_to_chunk):
            chunks = splitter.split_text(doc["text"])
            
            for chunk_idx, chunk_text in enumerate(chunks):
                chunk_id = f"{doc_id}_{doc_idx}_{chunk_idx}" # Unique ID
                
                embedding = llm_service.generate_embedding(chunk_text)
                
                chunk_metadata = {
                    "chunk_index": chunk_idx,
                    "doc_id": doc_id,
                    **doc["metadata"] # includes all table-specific and rbac metadata
                }
                
                all_chunk_ids.append(chunk_id)
                all_texts.append(chunk_text)
                all_embeddings.append(embedding)
                all_metadatas.append(chunk_metadata)

        # 4. Save to Vector DB
        vectordb_service.collection.add(
            ids=all_chunk_ids,
            documents=all_texts,
            embeddings=all_embeddings,
            metadatas=all_metadatas
        )

        return json.dumps({
            "success": True,
            "doc_id": doc_id,
            "table_name": table_name,
            "records_processed": len(rows),
            "total_chunks_saved": len(all_chunk_ids),
            "rbac_namespace": rbac_namespace
        })
        
    except Exception as e:
        import traceback
        return json.dumps({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    
@tool
def record_agent_memory_tool(agent_name: str, memory_key: str, memory_value: str, 
                             memory_type: str = "context") -> str:
    """
    Store general agent memory/context/logs for future retrievals and debugging.
    
    Args:
        agent_name (str): The name of the agent logging the memory.
        memory_key (str): A key to identify the memory content.
        memory_value (str): The content to be stored.
        memory_type (str): Type of memory (e.g., "context", "log", "decision").

    Returns:
        JSON with 'success' status.
    """
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
        return json.dumps({"success": False, "error": str(e)})