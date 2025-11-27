# LangGraph RAG Agent - Tool Usage Reference

## Overview
The LangGraphRAGAgent uses a sophisticated workflow-based architecture with three main graphs:
1. **Ingestion Graph** - Processes documents from various sources
2. **Retrieval Graph** - Answers questions using stored knowledge
3. **Optimization Graph** - Fine-tunes system performance

---

## 🔄 INGESTION WORKFLOW

**When to use:** When importing new documents, PDFs, tables, or text files into the RAG system.

**Flow:** Document → Metadata Extraction → Chunking → Vector Embedding → Persistence → Audit Log

### Step 1: Extract Document Text (Optional)
```
Tool: extract_document_text_tool (from ingestion_tools.py)
When: Before metadata extraction if raw document needs processing
Input: file_path, file_type ("auto", "pdf", "text", "word")
Output: Extracted raw text with metadata
```

### Step 2: Extract Metadata
```
Tool: extract_metadata_tool
When: After obtaining raw document text
Input: text, llm_service
Output: JSON with title, summary, keywords, topics, doc_type
Uses LLM: Yes - generates structured metadata using language model
Prompt Logic: Analyzes document to extract high-level semantic information
```

### Step 3: Chunk Document
```
Tool: chunk_document_tool
When: After metadata extraction
Input: text, doc_id, strategy ("recursive"), chunk_size (500), overlap (50)
Output: List of semantic chunks with chunk_ids
Strategy: RecursiveCharacterTextSplitter with separators for Markdown/structure
```

### Step 4: Save to VectorDB
```
Tool: save_to_vectordb_tool
When: After chunking
Input: chunks (JSON), doc_id, llm_service, vectordb_service, metadata, rbac_namespace
Process:
  1. Parses chunk metadata
  2. Generates embeddings for each chunk using LLM
  3. Stores embeddings in ChromaDB
  4. Persists metadata to SQLite (if DocumentMetadataModel available)
Output: JSON with chunks_saved count and VDB details
```

### Step 5: Update Metadata Tracking
```
Tool: update_metadata_tracking_tool
When: After VectorDB persistence
Input: doc_id, source_path, rbac_namespace, metadata, chunks_saved, is_table
Process:
  1. Records ingestion audit trail
  2. Updates DocumentTrackingModel in SQLite (if available)
  3. Marks document as COMPLETED
Output: JSON with success status
```

### Table Ingestion Path
```
Tool: ingest_sqlite_table_tool
When: Ingesting data from SQLite database tables
Input: table_name, doc_id, rbac_namespace, text_columns, metadata_columns, db_path, chunk_size, overlap
Process:
  1. Reads rows from specified table
  2. Extracts text from configured columns
  3. Chunks text with metadata from metadata_columns
  4. Generates embeddings for each chunk
  5. Saves to VectorDB and SQLite
Output: JSON with table_name, records_processed, chunks_saved
```

### Folder Ingestion Path
```
Tool: ingest_documents_from_path_tool
When: Batch ingesting multiple documents from a folder
Input: path, doc_id_prefix ("doc"), file_type ("auto", "pdf", "text", "word"), recursive (True)
Process:
  1. Discovers all files matching type in path (recursively optional)
  2. Generates doc_ids using format: {prefix}_{stem}_{timestamp}
  3. Returns list of discovered documents with file_type
Note: This is a DISCOVERY tool - does NOT perform extraction
Output: JSON with discovered_documents list containing file_path, file_type, doc_id, size_kb
```

### Agent Memory Logging
```
Tool: record_agent_memory_tool
When: Optional - storing agent decision logs and context
Input: agent_name, memory_key, memory_value, memory_type ("context", "log", "decision", "performance")
Process: Stores in AgentMemoryModel for agent self-reflection
```

---

## 🔍 RETRIEVAL WORKFLOW

**When to use:** When answering questions about ingested documents.

**Flow:** Question → Context Retrieval → Reranking → Quality Check → Answer Generation → Traceability

### Step 1: Retrieve Context
```
Tool: retrieve_context_tool (from retrieval_tools.py)
When: Question is received
Input: question, llm_service, vectordb_service, k=5
Process:
  1. Generates embedding for question using LLM
  2. Performs semantic similarity search in VectorDB
  3. Retrieves top-k (5) most similar chunks
Output: JSON with context list containing text, metadata, similarity scores
Debug Output: Shows retrieved documents in verbose/internal modes
```

### Step 2: Rerank Context
```
Tool: rerank_context_tool (from retrieval_tools.py)
When: After initial retrieval
Input: context (JSON), llm_service
Process:
  1. Uses LLM to re-evaluate relevance of retrieved chunks
  2. Reorders by relevance score
  3. Filters out low-relevance items
Output: JSON with reranked_context sorted by relevance
Debug Output: Shows relevance scores for top-3 documents in verbose mode
```

### Step 3: Check if Optimization Needed
```
Decision Node: check_optimization_needed (RL-based or heuristic)
When: Before answer generation
Logic:
  - If RL Healing Agent available: recommends SKIP, REINDEX, or RE_EMBED
  - Otherwise: Uses heuristic (quality < 0.6 or results < 3)
Output: should_optimize boolean, optimization_reason, rl_action
```

### Step 4: Optimize Context (if needed)
```
Tool: get_context_cost_tool (from healing_tools.py)
When: If should_optimize is True
Input: context list, llm_service, model_name
Output: estimated_cost_usd, total_tokens

Tool: optimize_chunk_size_tool (from healing_tools.py)
When: After cost analysis
Input: performance_history, llm_service
Process:
  1. Analyzes historical performance metrics
  2. Suggests optimal chunk_size and k parameters
Output: suggested_params with improved configuration
```

### Step 5: Generate Answer
```
Tool: answer_question_tool (from retrieval_tools.py)
When: After reranking and optional optimization
Input: question, context (JSON), llm_service
Process:
  1. Uses LLM to synthesize answer from reranked context
  2. Formats response based on response_mode
  3. Logs query metrics to RAGHistoryModel
Output: Answer text
Debug Output: Shows word count and preview in verbose mode
```

### Step 6: Generate Traceability
```
Tool: traceability_tool (from retrieval_tools.py)
When: After answer generation
Input: question, context, vectordb_service
Process:
  1. Creates audit trail linking question to sources
  2. Records chunk_ids, doc_ids, and relevance scores
  3. Stores lineage information
Output: JSON with traceability metadata
```

### Guardrails Validation
```
Applied in: ask_question() method

Concise Mode:
  - Validators: hallucination_check(), security_incident_policy()
  - Purpose: Ensure answer is accurate, safe, and policy-compliant
  - User: End-users getting sanitized responses

Internal Mode:
  - Validators: hallucination_check()
  - Purpose: Check accuracy for system integration
  - User: Other systems/services consuming the API

Verbose Mode:
  - Validators: None (raw data for debugging)
  - Purpose: Engineers need unfiltered data
  - User: RAG admins and developers
```

---

## 📊 OPTIMIZATION WORKFLOW

**When to use:** When system needs performance tuning based on historical metrics.

**Flow:** Performance History → Optimization Analysis → Config Update

### Step 1: Optimize System
```
Tool: optimize_chunk_size_tool
When: Called from optimize_system() method
Input: performance_history, llm_service
Process: Analyzes metrics and suggests better parameters
Output: JSON with optimization_result and suggested_params
```

### Step 2: Apply Configuration
```
Tool: adjust_config_tool
When: After optimization recommendations
Input: config_service (None if unavailable), updates
Process: Attempts to apply config changes to system
Output: JSON with config_result
```

---

## 🎯 OPERATION MODES

### Via invoke() method:

```python
# Ingest a single document
agent.invoke("ingest_document", text="...", doc_id="doc_123")

# Ingest from database table
agent.invoke("ingest_sqlite_table", table_name="knowledge_base", 
             doc_id="sqlite_kb", text_columns=["content"], 
             metadata_columns=["title", "category"])

# Ingest from file path/folder
agent.invoke("ingest_from_path", path="./docs", doc_id_prefix="doc",
             file_type="auto", recursive=True)

# Answer a question
agent.invoke("ask_question", question="What is...", response_mode="concise")

# Optimize system
agent.invoke("optimize", performance_history=[...], config_updates={...})
```

---

## 🔍 RESPONSE MODES

### Concise Mode
- **When:** End-user queries
- **Output:** Answer only + guardrails validation
- **Includes:** success, question, answer, session_id, guardrails_applied, errors
- **Excludes:** Verbose metadata, source documents, traceability

### Internal Mode
- **When:** System-to-system integration
- **Output:** Clean answer + structured metadata for database updates
- **Includes:** answer, quality_score, sources_count, source_docs, metadata, guardrails_applied
- **Uses:** hallucination_check guardrails only

### Verbose Mode
- **When:** Engineering/debugging
- **Output:** Complete business intelligence
- **Includes:** All metadata, traceability, RL recommendations, optimization details
- **Excludes:** Guardrails (raw data for analysis)
- **Debug Output:** Detailed logs for each node execution

---

## 📝 DEBUG OUTPUT

**Enabled in verbose and internal modes:**

Ingestion Nodes:
- ✓ Extract text success, method used
- ✓ Metadata extraction results
- ✓ Chunk count and strategy
- ✓ VectorDB save results
- ✓ Database tracking updates

Retrieval Nodes:
- ✓ Retrieved document count and quality score
- ✓ Reranking results with relevance scores
- ✓ Optimization decision and reason
- ✓ Answer generation word count
- ✓ Query logging to database
- ✓ Traceability generation

---

## 📋 TOOL DEPENDENCY MATRIX

| Tool | Requires | Optional | Fallback |
|------|----------|----------|----------|
| extract_metadata_tool | llm_service | - | Returns basic metadata |
| chunk_document_tool | - | - | Always works |
| save_to_vectordb_tool | llm_service, vectordb_service | DocumentMetadataModel | Skips SQLite save |
| update_metadata_tracking_tool | - | DocumentTrackingModel | Logs warning, continues |
| retrieve_context_tool | llm_service, vectordb_service | - | Fails gracefully |
| rerank_context_tool | llm_service | - | Skips reranking if LLM fails |
| answer_question_tool | llm_service | - | Returns error message |
| Guardrails validation | guardrails package | - | Skips validation if not installed |
| RL Healing Agent | - | RLHealingAgent | Uses heuristic instead |

---

## ✅ TOOL CHECKLIST

**Ingestion Tools (All Implemented):**
- ✅ extract_metadata_tool
- ✅ chunk_document_tool
- ✅ save_to_vectordb_tool
- ✅ update_metadata_tracking_tool
- ✅ ingest_sqlite_table_tool
- ✅ ingest_documents_from_path_tool
- ✅ extract_document_text_tool
- ✅ record_agent_memory_tool

**Retrieval Tools (All Implemented):**
- ✅ retrieve_context_tool
- ✅ rerank_context_tool
- ✅ answer_question_tool
- ✅ traceability_tool

**Healing/Optimization Tools (All Implemented):**
- ✅ check_embedding_health_tool
- ✅ get_context_cost_tool
- ✅ optimize_chunk_size_tool
- ✅ adjust_config_tool

---

## 🚨 ERROR HANDLING

- All tools are invoked with try-except blocks
- Errors are accumulated in state["errors"]
- Failed steps don't abort workflow (graceful degradation)
- Database model imports wrapped in try-except (optional)
- Guardrails wrapped in try-except (optional dependency)
- Fallback behaviors defined for each optional component

---

## 📖 CONFIGURATION SOURCE

All configuration comes from: `src/incident_iq/rag/config/data_sources.json`

Sections:
- `data_sources.pdf` - PDF extraction settings
- `data_sources.text` - Text file settings
- `data_sources.word` - Word document settings
- `document_paths` - Folder scanning settings
- `guardrails` - Response validation policies per mode
