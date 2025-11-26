#!/usr/bin/env python3
"""
METADATA SAVING FLOW ANALYSIS
Comprehensive view of how metadata is currently saved in SQLite through agents and tools
"""

# =============================================================================
# CURRENT METADATA SAVING ARCHITECTURE
# =============================================================================

current_flow = """
┌─────────────────────────────────────────────────────────────────────────────┐
│                    METADATA SAVING ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────┘

1. INGESTION FLOW (Through LangGraph Agent)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   LangGraphRAGAgent.ingest_document()
   │
   ├─→ ingestion_graph.invoke()
   │
   ├─→ Node 1: extract_metadata_node
   │   └─→ extract_metadata_tool (TOOL)
   │       • Input: raw document text
   │       • LLM: Structured extraction of metadata
   │       • Output: {"success": True, "metadata": {...}}
   │       • Saves to: STATE (not to SQLite)
   │
   ├─→ Node 2: chunk_document_node
   │   └─→ chunk_document_tool (TOOL)
   │       • Input: document text, doc_id, strategy, chunk_size
   │       • Process: RecursiveCharacterTextSplitter
   │       • Output: {"success": True, "chunks": [...]}
   │       • Saves to: STATE (not to SQLite)
   │
   ├─→ Node 3: save_vectordb_node
   │   └─→ save_to_vectordb_tool (TOOL)
   │       • Input: chunks, doc_id, metadata, rbac_namespace
   │       • Process: Generate embeddings + save to ChromaDB
   │       • Saves to: ChromaDB (Vector Database - NOT SQLite)
   │       • SQLite: NO direct save
   │
   └─→ Node 4: update_tracking_node
       └─→ update_metadata_tracking_tool (TOOL)
           • Input: doc_id, source_path, rbac_namespace, metadata, chunks_saved
           • Process: Call DocumentTrackingModel
           • Saves to: SQLite (via DocumentTrackingModel)
           • Table: document_metadata_tracking (legacy table)
           • Status: OPTIONAL (only if DocumentTrackingModel exists)

   RESULT: 
   ✓ ChromaDB: Has all chunks with embeddings and metadata
   ✓ SQLite: document_metadata_tracking table updated (if model exists)
   ✗ SQLite: New optimized schema tables (document_metadata, chunk_embedding_data) NOT populated


2. RETRIEVAL FLOW (Through LangGraph Agent)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   LangGraphRAGAgent.ask_question()
   │
   ├─→ retrieval_graph.invoke()
   │
   ├─→ Node 1: retrieve_context_node
   │   └─→ retrieve_context_tool
   │       • Queries ChromaDB for relevant chunks
   │       • No SQLite writes
   │
   ├─→ Node 2: rerank_context_node
   │   └─→ rerank_context_tool
   │       • Reranks retrieved context
   │       • No SQLite writes
   │
   ├─→ Node 3: generate_answer_node
   │   └─→ generate_answer_tool
   │       • Generates final answer using LLM
   │       • No SQLite writes
   │
   └─→ Node 4: (optional) record_agent_memory_tool
       • Input: agent_name, memory_key, memory_value, memory_type
       • Saves to: SQLite (via AgentMemoryModel)
       • Table: agent_memory (legacy table)
       • Note: NOT called in current retrieval graph


3. CURRENT SQLITE TABLES BEING UPDATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   INGESTION:
   ├─ document_metadata_tracking (via DocumentTrackingModel)
   │  └─ Fields: document_id, source_path, rbac_namespace, doc_type, 
   │             chunks_saved, ingestion_date, ingestion_status, metadata_tags
   │
   RETRIEVAL:
   ├─ agent_memory (via AgentMemoryModel - optional)
   │  └─ Fields: agent_id, memory_type, content, importance_score, created_at
   │
   OPTIMIZATION:
   └─ (none currently tracked)


4. OPTIMIZED SCHEMA TABLES (Currently NOT being used)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   NEW TABLES (created but empty):
   ├─ document_metadata
   │  └─ doc_id, title, author, source, summary, rbac_namespace, 
   │     chunk_strategy, chunk_size_char, overlap_char, metadata_json, last_ingested
   │
   ├─ chunk_embedding_data
   │  └─ chunk_id, doc_id, embedding_model, embedding_version, quality_score,
   │     reindex_count, healing_suggestions, created_at, last_healed
   │  └─ Foreign Key: doc_id → document_metadata.doc_id
   │
   └─ rag_history_and_optimization
      └─ history_id, event_type, timestamp, query_text, target_doc_id,
         target_chunk_id, metrics_json, context_json, reward_signal,
         action_taken, state_before, state_after, agent_id, user_id, session_id
      └─ Foreign Key: target_doc_id → document_metadata.doc_id


5. DATA FLOW SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Document Input
      ↓
   extract_metadata_tool (TOOL)
      ↓
   chunk_document_tool (TOOL)
      ↓
   save_to_vectordb_tool (TOOL)
      ├─→ ChromaDB ✓ (full chunks with embeddings)
      └─→ (optionally) update_metadata_tracking_tool (TOOL)
          └─→ SQLite ✓ (document_metadata_tracking - legacy table)
      
   Querying
      ↓
   retrieve_context_tool (TOOL)
      ├─→ ChromaDB ✓ (retrieves via vector search)
      └─→ (optionally) record_agent_memory_tool (TOOL)
          └─→ SQLite ✓ (agent_memory - legacy table)


6. PROBLEM ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   ✓ GOOD: Tools are modular and reusable
   ✓ GOOD: LangGraph orchestrates the workflow
   ✓ GOOD: Metadata extracted via LLM structured output
   
   ✗ PROBLEM 1: New optimized schema tables are empty
      → Migration created the tables but no data is written
      → Tools are still using old DocumentTrackingModel
      → New tables (document_metadata, chunk_embedding_data, rag_history_and_optimization)
        are never populated
   
   ✗ PROBLEM 2: Metadata only saved to ChromaDB, not to relational SQLite
      → Document-level metadata not in relational format for queries
      → Chunk quality scores not tracked in SQLite
      → Query history not logged in SQLite
      → Can't easily query metadata relationships
   
   ✗ PROBLEM 3: Tools don't use the new models
      → DocumentMetadataModel not called
      → ChunkEmbeddingDataModel not called
      → RAGHistoryModel not called
      → Optimization/healing decisions not logged
"""

print(current_flow)

# =============================================================================
# SOLUTION APPROACH
# =============================================================================

solution = """

┌─────────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED SOLUTION                                     │
└─────────────────────────────────────────────────────────────────────────────┘

OPTION 1: Update Tools to Use New Models (RECOMMENDED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Modify: save_to_vectordb_tool
   ├─→ After saving to ChromaDB:
   │   ├─→ Extract doc-level metadata
   │   ├─→ Create DocumentMetadataModel entry
   │   └─→ Create ChunkEmbeddingDataModel entries (one per chunk)
   │
   └─→ Benefits:
       ✓ document_metadata table populated
       ✓ chunk_embedding_data table populated
       ✓ Chunk quality scores tracked
       ✓ Relational queries possible


OPTION 2: Add Query Tracking to Retrieval Flow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Modify: ask_question workflow
   ├─→ After retrieval & reranking:
   │   ├─→ Create RAGHistoryModel entry with event_type="QUERY"
   │   └─→ Log metrics: retrieval_quality, latency, source_documents
   │
   └─→ Benefits:
       ✓ rag_history_and_optimization table populated
       ✓ Query patterns tracked
       ✓ Performance metrics logged


OPTION 3: Add Healing/Optimization Tracking
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Modify: optimization nodes in retrieval graph
   ├─→ When healing is applied:
   │   ├─→ Create RAGHistoryModel entry with event_type="HEAL"
   │   └─→ Log: strategy, before_metrics, after_metrics
   │
   └─→ Benefits:
       ✓ Healing operations tracked
       ✓ RL learning signals captured
       ✓ Optimization history maintained


IMPLEMENTATION STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Step 1: Create/Update DatabaseModel classes
   ├─ DocumentMetadataModel (maps to document_metadata)
   ├─ ChunkEmbeddingDataModel (maps to chunk_embedding_data)
   └─ RAGHistoryModel (maps to rag_history_and_optimization)

   Step 2: Update save_to_vectordb_tool
   ├─ After ChromaDB save, create DocumentMetadataModel entry
   └─ For each chunk, create ChunkEmbeddingDataModel entry

   Step 3: Add Query Tracking
   ├─ Create new tool: save_query_history_tool
   └─ Call after answer generation in ask_question

   Step 4: Add Healing Tracking
   ├─ Modify optimization nodes
   └─ Log healing decisions to rag_history_and_optimization

   Step 5: Test End-to-End
   ├─ Run ingestion → verify document_metadata populated
   ├─ Run query → verify rag_history_and_optimization populated
   └─ Run optimization → verify healing logs created
"""

print(solution)

print("\n" + "=" * 80)
print("KEY FILES TO CHECK/MODIFY:")
print("=" * 80)
print("""
1. src/incident_iq/rag/tools/ingestion_tools.py
   └─ save_to_vectordb_tool (ADD SQLite writes)
   └─ NEW TOOL: save_query_history_tool (ADD for retrieval tracking)

2. src/incident_iq/rag/agents/langgraph_agent/langgraph_rag_agent.py
   └─ _build_ingestion_graph (may need updates after tool changes)
   └─ _build_retrieval_graph (ADD query tracking)
   └─ _build_optimization_graph (ADD healing tracking)

3. src/incident_iq/database/models/
   ├─ document_metadata_model.py (CREATE if doesn't exist)
   ├─ chunk_embedding_data_model.py (CREATE)
   └─ rag_history_model.py (CREATE)

4. scripts/
   ├─ run_optimized_migration.py (DONE ✓)
   ├─ check_database.py (DONE ✓)
   └─ NEW: populate_from_ingestion.py (populate with test data)
""")
