DATABASE CAPTURE PROBLEM ANALYSIS
==================================================

PROBLEM STATEMENT
==================================================
✗ All 3 optimized schema tables are EMPTY (0% data capture)
  - document_metadata: 0 rows
  - chunk_embedding_data: 0 rows  
  - rag_history_and_optimization: 0 rows

ROOT CAUSE ANALYSIS
==================================================

The code to populate these tables EXISTS but is NOT BEING CALLED.

Evidence:
1. File: src/incident_iq/rag/tools/ingestion_tools.py
   Function: save_to_vectordb_tool()
   
   Has code sections for SQLite writes (after ChromaDB save):
   
   Lines ~380-450:
   ```python
   # NEW: Also write to SQLite tables after ChromaDB save
   try:
       # Create DocumentMetadataModel entry
       from ...database.models.document_metadata_model import DocumentMetadataModel
       metadata_model = DocumentMetadataModel(db_path=db_path)
       metadata_model.create(
           doc_id=doc_id,
           title=extract_title(text),
           ...
       )
       
       # Create ChunkEmbeddingDataModel entry for each chunk
       from ...database.models.chunk_embedding_data_model import ChunkEmbeddingDataModel
       for chunk in chunks:
           embedding_model = ChunkEmbeddingDataModel(db_path=db_path)
           embedding_model.create(chunk_id=...)
   ```
   
   BUT: This code is NEVER REACHED because save_to_vectordb_tool is never called.


FIELD-BY-FIELD BREAKDOWN OF WHAT SHOULD BE CAPTURED
==================================================

1. DOCUMENT_METADATA (Should have 11 fields populated)
   
   Required Fields & Current Status:
   ├─ doc_id                [X] NEVER SET - Should be doc identifier
   ├─ title                 [X] NEVER SET - Should extract from document
   ├─ author                [X] NEVER SET - Should extract from document/metadata
   ├─ source                [X] NEVER SET - Should track where document came from
   ├─ summary               [X] NEVER SET - Should auto-generate or extract
   ├─ rbac_namespace        [X] NEVER SET - Should track access control
   ├─ chunk_strategy        [X] NEVER SET - Should log chunking method used (e.g., recursive_splitter)
   ├─ chunk_size_char       [X] NEVER SET - Should be 512 or configured value
   ├─ overlap_char          [X] NEVER SET - Should be chunk size * 0.1
   ├─ metadata_json         [X] NEVER SET - Should store tags, classifications
   └─ last_ingested         [X] NEVER SET - Should be current timestamp


2. CHUNK_EMBEDDING_DATA (Should have 9 fields, one per chunk)
   
   What it's for: Track health and quality of individual chunks
   
   Required Fields:
   ├─ chunk_id              [X] NEVER SET - Unique chunk identifier
   ├─ doc_id                [X] NEVER SET - Reference to parent document
   ├─ embedding_model       [X] NEVER SET - Should track model used (ollama, mistral, etc)
   ├─ embedding_version     [X] NEVER SET - Version of embedding model
   ├─ quality_score         [X] NEVER SET - Initial quality (0-1) or default 0.7
   ├─ reindex_count         [X] NEVER SET - Should be 0 on first creation
   ├─ healing_suggestions   [X] NEVER SET - JSON with improvement suggestions
   ├─ created_at            [X] NEVER SET - Timestamp of creation
   └─ last_healed           [X] NEVER SET - Null until first healing action


3. RAG_HISTORY_AND_OPTIMIZATION (Event log - should grow with queries)
   
   What it's for: Track all queries, healing actions, synthetic tests for RL learning
   
   Required Fields:
   ├─ history_id            [X] NEVER SET - Auto-increment
   ├─ event_type            [X] NEVER SET - Should be QUERY, HEAL, or SYNTHETIC_TEST
   ├─ timestamp             [X] NEVER SET - Event time
   ├─ query_text            [X] NEVER SET - Text of query (for QUERY events)
   ├─ target_doc_id         [X] NEVER SET - Which document queried/healed
   ├─ target_chunk_id       [X] NEVER SET - Which chunk (for healing)
   ├─ metrics_json          [X] NEVER SET - Contains cost_tokens, user_feedback, accuracy, etc
   ├─ context_json          [X] NEVER SET - Contains reasoning, alternatives, etc
   ├─ reward_signal         [X] NEVER SET - RL reward (for HEAL events)
   ├─ action_taken          [X] NEVER SET - Which action (SKIP, OPTIMIZE, REINDEX, RE_EMBED)
   ├─ state_before          [X] NEVER SET - State JSON before action
   ├─ state_after           [X] NEVER SET - State JSON after action
   ├─ agent_id              [X] NEVER SET - Which agent (langgraph_agent, rl_healing_agent)
   ├─ user_id               [X] NEVER SET - Who triggered it
   └─ session_id            [X] NEVER SET - Session tracking


WHERE DATA SHOULD BE CAPTURED
==================================================

1. INGESTION PHASE - Should populate document_metadata & chunk_embedding_data
   
   Current Flow (in langgraph_rag_agent.py - ingest_document method):
   
   a) extract_metadata_tool() - Extracts title, author, source
   b) chunk_document_tool() - Chunks text with parameters
   c) save_to_vectordb_tool() <- THIS SHOULD WRITE TO SQLITE
   
   Problem: save_to_vectordb_tool() is called but the SQLite write code
            exists but seems not to be executing


2. RETRIEVAL PHASE - Should populate rag_history_and_optimization (QUERY events)
   
   Current Flow (in langgraph_rag_agent.py - ask_question method):
   
   a) retrieve_context_tool() - Gets context
   b) rerank_context_tool() - Orders by relevance
   c) [RL Agent Decision Node] - Decides on healing
   d) answer_question_tool() - Generates answer
   e) [Should call RAGHistoryModel.log_query()] <- NOT IMPLEMENTED
   
   Problem: No call to log_query() to track the query event


3. HEALING PHASE - Should populate rag_history_and_optimization (HEAL events)
   
   Current Flow (in langgraph_rag_agent.py - optimization nodes):
   
   a) RL agent recommend_healing() - Decides action
   b) Apply the action (optimize, reindex, re-embed)
   c) Measure reward
   d) [Should call RAGHistoryModel.log_healing()] <- NOT IMPLEMENTED
   e) rl_healing_agent.observe_reward() - Updates RL
   
   Problem: No call to log_healing() to track healing events


WHAT NEEDS TO BE FIXED
==================================================

PRIORITY 1: Debug why save_to_vectordb_tool SQLite writes aren't executing
  File: src/incident_iq/rag/tools/ingestion_tools.py
  Function: save_to_vectordb_tool()
  Action: Add debug logging to trace execution

PRIORITY 2: Add RAGHistoryModel.log_query() call after answer generation
  File: src/incident_iq/rag/agents/langgraph_agent/langgraph_rag_agent.py
  Function: answer_question_node()
  Action: After answer generated, log the query event to rag_history_and_optimization

PRIORITY 3: Add RAGHistoryModel.log_healing() call after healing action
  File: src/incident_iq/rag/agents/langgraph_agent/langgraph_rag_agent.py
  Function: optimize_context_node() or after healing applied
  Action: Log healing event with metrics and reward signal

PRIORITY 4: Verify save_to_vectordb_tool is called during ingestion
  File: scripts/test_langgraph_with_healing.py
  Action: Run test with verbose logging to confirm SQLite writes


EXPECTED OUTCOME AFTER FIX
==================================================

After these fixes:

1. document_metadata should have:
   - 1 row per ingested document
   - All 11 fields populated for each document

2. chunk_embedding_data should have:
   - 1 row per chunk generated from documents
   - All 9 fields populated for tracking quality and reindexing

3. rag_history_and_optimization should have:
   - 1 QUERY row for each user query
   - 1 HEAL row for each healing action taken by RL agent
   - 1 SYNTHETIC_TEST row for each test query
   - All metrics, rewards, and context captured for RL learning


CURRENT BLOCKING ISSUES
==================================================

1. save_to_vectordb_tool's SQLite code may have errors being silently caught
   Solution: Add debug logging and error visibility

2. RAGHistoryModel.log_query/log_healing never called in the pipeline
   Solution: Add these calls to the appropriate LangGraph nodes

3. No way to verify if data is being written without running full pipeline
   Solution: Run analyze_captures.py after each test

