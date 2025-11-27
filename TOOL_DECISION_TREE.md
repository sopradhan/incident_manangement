# LangGraph RAG Agent - Tool Decision Tree

## 🎯 Which Tool to Use When?

```
START: You have a task
│
├─ INGESTING NEW CONTENT?
│  │
│  ├─ Single Document (raw text)?
│  │  └─→ agent.invoke("ingest_document", text="...", doc_id="doc_123")
│  │     TOOLS USED (in order):
│  │     1. extract_metadata_tool (LLM analyzes text → metadata)
│  │     2. chunk_document_tool (splits into chunks)
│  │     3. save_to_vectordb_tool (generates embeddings → VectorDB)
│  │     4. update_metadata_tracking_tool (audit trail)
│  │
│  ├─ Database Table?
│  │  └─→ agent.invoke("ingest_sqlite_table", 
│  │                    table_name="kb", 
│  │                    text_columns=["content"],
│  │                    metadata_columns=["title"])
│  │     TOOLS USED: ingest_sqlite_table_tool
│  │     (handles chunking, embedding, and storage internally)
│  │
│  └─ Multiple Files from Folder?
│     └─→ agent.invoke("ingest_from_path",
│                      path="./docs",
│                      file_type="auto",
│                      recursive=True)
│        TOOLS USED:
│        1. ingest_documents_from_path_tool (discovers files, generates doc_ids)
│        2. For each discovered file:
│           a. extract_metadata_tool
│           b. chunk_document_tool
│           c. save_to_vectordb_tool
│           d. update_metadata_tracking_tool
│
│
├─ ANSWERING A QUESTION?
│  │
│  └─→ agent.invoke("ask_question",
│                   question="What is...",
│                   response_mode="concise"|"internal"|"verbose")
│     TOOLS USED (in sequence):
│     1. retrieve_context_tool (semantic search → top-5 docs)
│     2. rerank_context_tool (LLM-based relevance sorting)
│     3. [DECISION] Is optimization needed?
│     │  ├─ YES → get_context_cost_tool + optimize_chunk_size_tool
│     │  └─ NO  → skip to answer
│     4. answer_question_tool (synthesize answer from context)
│     5. traceability_tool (audit trail of sources)
│     6. [GUARDRAILS] Apply validation based on response_mode:
│        ├─ concise: hallucination_check + security_incident_policy
│        ├─ internal: hallucination_check
│        └─ verbose: no guardrails (raw data)
│
│
├─ OPTIMIZING SYSTEM PERFORMANCE?
│  │
│  └─→ agent.invoke("optimize",
│                   performance_history=[...],
│                   config_updates={...})
│     TOOLS USED:
│     1. optimize_chunk_size_tool (analyze metrics)
│     2. adjust_config_tool (apply recommendations)
│
│
└─ DONE
```

---

## 📊 Tool Compatibility Matrix

| Task | Primary Tool | Depends On | Fallback | Optional |
|------|-------------|-----------|----------|----------|
| Extract text from PDF | extract_document_text_tool | pdfplumber/PyPDF2 | PyPDF2 if pdfplumber fails | - |
| Generate metadata | extract_metadata_tool | llm_service | Basic metadata | - |
| Split document | chunk_document_tool | - | Always works | - |
| Create embeddings | save_to_vectordb_tool | llm_service | Fail gracefully | DocumentMetadataModel |
| Search documents | retrieve_context_tool | llm_service + vectordb_service | Fail gracefully | - |
| Re-score results | rerank_context_tool | llm_service | Uses raw scores if fails | - |
| Generate answer | answer_question_tool | llm_service | Returns error | - |
| Analyze cost | get_context_cost_tool | llm_service | Returns default | - |
| Suggest config | optimize_chunk_size_tool | - | Returns no suggestions | - |
| Apply config | adjust_config_tool | - | Always succeeds (no-op) | ConfigService |
| Check healing | check_embedding_health_tool | vectordb_service | Reports "unknown" | - |
| Log query | RAGHistoryModel | - | Logs warning | - |
| Validate answer | Guard (guardrails) | guardrails package | Skip validation | Hallucination/Security check |

---

## 🔄 Workflow Sequences

### Sequence 1: Ingest Single Document
```
User calls: agent.invoke("ingest_document", text="...", doc_id="doc_1")
↓
ingestion_graph.invoke(initial_state)
│
├→ extract_metadata_node
│  └→ extract_metadata_tool.invoke(text, llm_service)
│     • LLM analyzes document
│     • Outputs: title, summary, keywords, topics, doc_type
│
├→ chunk_document_node
│  └→ chunk_document_tool.invoke(text, doc_id)
│     • Splits text using RecursiveCharacterTextSplitter
│     • Outputs: list of chunks with chunk_ids
│
├→ save_vectordb_node
│  └→ save_to_vectordb_tool.invoke(chunks, doc_id, llm_service, vectordb_service, metadata)
│     • For each chunk: generate embedding via llm_service
│     • Store in ChromaDB with chunk_id
│     • Persist to SQLite (if model available)
│     • Outputs: chunks_saved count
│
└→ update_tracking_node
   └→ update_metadata_tracking_tool.invoke(doc_id, source_path, metadata, chunks_saved)
      • Records audit trail in DocumentTrackingModel
      • Marks ingestion_status = COMPLETED
      • Outputs: success status
```

### Sequence 2: Answer Question
```
User calls: agent.invoke("ask_question", question="What is...", response_mode="concise")
↓
retrieval_graph.invoke(initial_state)
│
├→ retrieve_context_node
│  └→ retrieve_context_tool.invoke(question, llm_service, vectordb_service, k=5)
│     • Generate question embedding
│     • Semantic search in VectorDB
│     • Return top-5 most similar chunks
│     • Compute retrieval_quality = len(results)/5
│
├→ rerank_context_node
│  └→ rerank_context_tool.invoke(context, llm_service)
│     • LLM re-evaluates relevance of each chunk
│     • Reorder by relevance score
│     • Filter low-confidence matches
│
├→ check_optimization (decision node)
│  • If quality < 0.6 OR results < 3: should_optimize = True
│  • Else: should_optimize = False
│
├→ [IF should_optimize = True]
│  ├→ get_context_cost_tool.invoke(context, llm_service, "ollama")
│  │  • Estimate tokens and cost
│  │
│  └→ optimize_chunk_size_tool.invoke(performance_history, llm_service)
│     • Analyze historical metrics
│     • Suggest better parameters
│
├→ answer_question_node
│  └→ answer_question_tool.invoke(question, context, llm_service)
│     • LLM synthesizes answer from reranked context
│     • Applies response_mode formatting
│     • Applies guardrails validation (if needed)
│
├→ traceability_node
│  └→ traceability_tool.invoke(question, context, vectordb_service)
│     • Creates audit trail
│     • Records source chunk_ids and doc_ids
│     • Outputs: traceability metadata
│
└→ ask_question() method applies guardrails
   ├─ If response_mode = "concise":
   │  └─ _apply_guardrails_validation(answer, "concise")
   │     • Guards: hallucination_check() + security_incident_policy()
   │     • Returns: validated_answer or original if validation fails
   │
   ├─ If response_mode = "internal":
   │  └─ _apply_guardrails_validation(answer, "internal")
   │     • Guards: hallucination_check() only
   │     • Returns: validated_answer
   │
   └─ If response_mode = "verbose":
      └─ No guardrails (engineers need raw data)
         • Returns: raw answer with all metadata
```

### Sequence 3: Ingest Folder of Documents
```
User calls: agent.invoke("ingest_from_path", path="./docs", file_type="auto", recursive=True)
↓
invoke() method processes "ingest_from_path" operation
│
├→ ingest_documents_from_path_tool.invoke(path, doc_id_prefix, file_type, recursive)
│  │
│  ├─ Scans path recursively for files matching type
│  ├─ Generates doc_id for each: {prefix}_{stem}_{timestamp}
│  ├─ Returns list of discovered documents
│  └─ NOTE: This tool ONLY discovers, does NOT extract
│
├→ For each discovered_document in discovered_documents:
│  │
│  ├─ Extract document text (if needed)
│  │  └─→ extract_document_text_tool.invoke(file_path, file_type)
│  │
│  └─ Call ingest_document(text, doc_id) for that file
│     └─ Runs full ingestion_graph (metadata → chunks → embeddings → tracking)
│
└─ Returns summary: documents_discovered, documents_ingested, documents_failed
```

---

## ⚡ Performance Optimization Triggers

### When get_context_cost_tool is used:
- **Trigger:** After reranking context, if should_optimize = True
- **Reason:** Estimate token cost of LLM call
- **Output:** estimated_cost_usd, total_tokens
- **Next Step:** Use info for budget-aware decisions

### When optimize_chunk_size_tool is used:
- **Trigger:** After cost analysis, if should_optimize = True
- **Reason:** Suggest better chunking parameters
- **Output:** suggested_params (chunk_size, overlap, k)
- **Next Step:** adjust_config_tool applies these

### When adjust_config_tool is used:
- **Trigger:** From optimize_system() when explicitly called
- **Reason:** Persist optimization recommendations
- **Output:** config_result with applied settings
- **Note:** If ConfigService unavailable, silently skips

---

## 🛡️ Guardrails Decision Logic

**Location:** `_apply_guardrails_validation()` method

```
Input: answer (str), response_mode (str)

If HAS_GUARDRAILS = False:
  └─ Return: {"validated": True, "guardrails_applied": False}

If response_mode = "verbose":
  └─ Return: {"validated": True, "guardrails_applied": False}

If response_mode = "concise":
  └─ Guard.validate(answer) with:
     • hallucination_check()
     • security_incident_policy()
     └─ Returns validated answer or original if fails

If response_mode = "internal":
  └─ Guard.validate(answer) with:
     • hallucination_check()
     └─ Returns validated answer or original if fails

On validation error:
  └─ Log warning, return original answer
     (fail-safe: don't break workflow)
```

---

## 🔌 API Usage Examples

### Example 1: Ingest PDF from Folder
```python
result = agent.invoke(
    "ingest_from_path",
    path="/home/user/documents",
    doc_id_prefix="knowledge_base",
    file_type="pdf",
    recursive=True
)
# Returns: {
#   "success": True,
#   "documents_discovered": 42,
#   "documents_ingested": 40,
#   "documents_failed": 2,
#   "errors": [...]
# }
```

### Example 2: Ask Question with Internal Mode
```python
result = agent.invoke(
    "ask_question",
    question="What are the main risks in the incident?",
    response_mode="internal",
    doc_id="incident_2024_001"
)
# Returns: {
#   "success": True,
#   "answer": "The main risks are...",
#   "quality_score": 0.85,
#   "sources_count": 3,
#   "source_docs": [...],
#   "metadata": {...},
#   "guardrails_applied": True
# }
```

### Example 3: Verbose Mode for Debugging
```python
result = agent.invoke(
    "ask_question",
    question="What happened?",
    response_mode="verbose"
)
# Console Output:
# [🔍 RETRIEVE CONTEXT NODE - VERBOSE MODE]
#   Question: What happened?...
#   Retrieving top-k=5 relevant documents...
#   ✓ Retrieved 5 documents (quality score: 1.00)
#   [1] Doc: incident_123 | The incident occurred when...
#   ...
#
# [📊 RERANK CONTEXT NODE - VERBOSE MODE]
#   Reranking 5 documents for relevance...
#   ✓ Reranked to 5 documents (sorted by relevance)
#   [1] Score: 0.98 | Doc: incident_123
#   ...
#
# [📋 ANSWER GENERATION NODE - VERBOSE MODE]
#   ...
```

---

## 🚨 Error Handling Strategy

**All tools wrapped in try-except:**

1. Tool fails → Error added to state["errors"]
2. Workflow continues (graceful degradation)
3. Later stages use degraded data
4. Final response includes error list
5. Response still succeeds if any data is generated

**Example:**
```
├─ retrieve_context_tool fails
│  └─ state["retrieval_quality"] = 0.0
│  └─ state["errors"] += "Context retrieval failed: ..."
│
├─ rerank_context_tool uses empty context
│  └─ Still completes
│
├─ answer_question_tool gets no context
│  └─ Generates answer without context
│
└─ Response includes:
   "success": False,
   "errors": ["Context retrieval failed: ..."],
   "answer": "I couldn't find relevant information..."
```

---

## 📋 Tool Status Summary

✅ **All 12+ Tools Implemented and Functional:**

**Ingestion Suite:**
- ✅ extract_metadata_tool - LLM-powered metadata extraction
- ✅ chunk_document_tool - Semantic text splitting
- ✅ save_to_vectordb_tool - Embedding generation and storage
- ✅ update_metadata_tracking_tool - Audit trail
- ✅ ingest_sqlite_table_tool - Database table ingestion
- ✅ ingest_documents_from_path_tool - Batch discovery
- ✅ extract_document_text_tool - Multi-format extraction
- ✅ record_agent_memory_tool - Agent self-reflection

**Retrieval Suite:**
- ✅ retrieve_context_tool - Semantic search
- ✅ rerank_context_tool - Relevance optimization
- ✅ answer_question_tool - Answer synthesis
- ✅ traceability_tool - Source attribution

**Optimization Suite:**
- ✅ check_embedding_health_tool - Vector DB health
- ✅ get_context_cost_tool - Token estimation
- ✅ optimize_chunk_size_tool - Parameter optimization
- ✅ adjust_config_tool - Configuration management

**All tools properly integrated with:**
- Response mode awareness (concise/internal/verbose)
- Error handling and graceful degradation
- Debug output for engineering visibility
- Guardrails validation where applicable
