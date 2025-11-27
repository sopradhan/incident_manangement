# LangGraph Agent Testing Guide

## Quick Start

### Option 1: Quick Test (Recommended First)
```bash
cd E:\ai-projects\incident_manangement
python test_agent_quick.py
```

This runs:
1. ✅ Agent initialization
2. ✅ Table ingestion (knowledge_base)
3. ✅ Question answering (concise mode)
4. ✅ Question answering (internal mode)
5. ✅ Question answering (verbose mode)

Expected output:
- Clean answers in concise mode
- Structured data + quality scores in internal mode
- Full debug details in verbose mode

### Option 2: Comprehensive Test
```bash
cd E:\ai-projects\incident_manangement
python test_agent_table_ingestion.py
```

This runs:
1. ✅ Tool availability verification
2. ✅ Table ingestion
3. ✅ Question answering (concise)
4. ✅ Question answering (internal)
5. ✅ Question answering (verbose)
6. ✅ Detailed test summary

---

## What's Being Tested

### Test 1: Table Ingestion
```python
result = agent.invoke(
    "ingest_sqlite_table",
    table_name="knowledge_base",
    doc_id="sqlite_knowledge_base",
    rbac_namespace="general",
    text_columns=["cause", "description", "impact", "remediation_steps", "rca"],
    metadata_columns=["id", "resource_type", "environment", "dollar_impact"]
)
```

**Configuration from data_sources.json:**
- Table: `knowledge_base`
- Text columns: cause, description, impact, remediation_steps, rca
- Metadata columns: id, resource_type, environment, dollar_impact

**Tools Used:**
1. `ingest_sqlite_table_tool` (main tool)
2. `extract_metadata_tool` (for each row)
3. `chunk_document_tool` (for chunking)
4. `save_to_vectordb_tool` (for embeddings)
5. `update_metadata_tracking_tool` (for audit trail)

**Expected Result:**
```json
{
  "success": true,
  "table_name": "knowledge_base",
  "records_processed": 42,
  "total_chunks_saved": 150,
  "rbac_namespace": "general"
}
```

---

### Test 2: Question Answering - CONCISE Mode
```python
result = agent.invoke(
    "ask_question",
    question="What are the main incident causes?",
    response_mode="concise"
)
```

**Response Mode: CONCISE**
- **User:** End-users
- **Output:** Clean answer only
- **Guardrails:** hallucination_check + security_incident_policy
- **Debug Output:** Minimal (suppressed)

**Expected Result:**
```json
{
  "success": true,
  "question": "What are the main incident causes?",
  "answer": "The main incident causes include...",
  "session_id": "uuid-string",
  "guardrails_applied": true,
  "errors": []
}
```

**Tools Used:**
1. `retrieve_context_tool` (semantic search)
2. `rerank_context_tool` (relevance sorting)
3. `answer_question_tool` (synthesis)
4. `traceability_tool` (audit trail)
5. Guardrails validation (hallucination + security)

---

### Test 3: Question Answering - INTERNAL Mode
```python
result = agent.invoke(
    "ask_question",
    question="What remediation steps are recommended?",
    response_mode="internal"
)
```

**Response Mode: INTERNAL**
- **User:** System/API consumers
- **Output:** Structured data + quality metrics
- **Guardrails:** hallucination_check only
- **Debug Output:** Node-level logs

**Expected Result:**
```json
{
  "success": true,
  "answer": "Remediation steps include...",
  "quality_score": 0.85,
  "sources_count": 3,
  "source_docs": [
    {"doc_id": "sqlite_knowledge_base", "chunk_id": "chunk_123"}
  ],
  "metadata": {
    "session_id": "uuid-string",
    "timestamp": 1234567890.123,
    "model": "langgraph_rag_agent",
    "execution_time_ms": 1500
  },
  "guardrails_applied": true,
  "errors": []
}
```

**Tools Used:**
1. `retrieve_context_tool` (with logging)
2. `rerank_context_tool` (with logging)
3. `answer_question_tool`
4. `traceability_tool`
5. Guardrails validation (hallucination only)

---

### Test 4: Question Answering - VERBOSE Mode
```python
result = agent.invoke(
    "ask_question",
    question="What are the environmental impacts?",
    response_mode="verbose"
)
```

**Response Mode: VERBOSE**
- **User:** Engineers/Admins/Debuggers
- **Output:** Full business intelligence
- **Guardrails:** NONE (raw data)
- **Debug Output:** Full node execution + console logs

**Console Output Example:**
```
[🔍 RETRIEVE CONTEXT NODE - VERBOSE MODE]
  Question: What are the environmental impacts?...
  Retrieving top-k=5 relevant documents...
  ✓ Retrieved 3 documents (quality score: 0.60)
  [1] Doc: sqlite_knowledge_base | The incident affected...

[📊 RERANK CONTEXT NODE - VERBOSE MODE]
  Reranking 3 documents for relevance...
  ✓ Reranked to 3 documents (sorted by relevance)
  [1] Score: 0.95 | Doc: sqlite_knowledge_base

[📋 ANSWER GENERATION NODE - VERBOSE MODE]
  Question: What are the environmental impacts?...
  Response Mode: verbose
  Reranked Context Items: 3
  ✓ Answer Generated (145 words)
  Answer Preview: Environmental impacts include...
```

**Expected Result:**
```json
{
  "success": true,
  "question": "What are the environmental impacts?",
  "answer": "Environmental impacts include...",
  "sources": [{"text": "...", "metadata": {...}}],
  "sources_count": 3,
  "traceability": {...},
  "retrieval_quality": 0.60,
  "optimization_applied": false,
  "optimization_reason": "Quality=0.60, Results=3",
  "rl_action": "SKIP",
  "execution_time_ms": 2100,
  "session_id": "uuid-string",
  "visualization_data": {...},
  "guardrails_applied": false,
  "errors": []
}
```

**Tools Used:**
1. `retrieve_context_tool` (with detailed output)
2. `rerank_context_tool` (with scores shown)
3. `answer_question_tool` (with metrics)
4. `traceability_tool` (full lineage)
5. Optional: `get_context_cost_tool`, `optimize_chunk_size_tool`

---

## Expected Tool Invocation Sequence

### Ingestion Flow
```
user calls: agent.invoke("ingest_sqlite_table", ...)
    ↓
ingest_sqlite_table_tool.invoke()
    ↓
For each row from table:
    ├─→ extract_metadata_tool (LLM analyzes)
    ├─→ chunk_document_tool (split text)
    ├─→ save_to_vectordb_tool (create embeddings)
    └─→ update_metadata_tracking_tool (audit trail)
    ↓
return: {success, records_processed, total_chunks_saved}
```

### Retrieval Flow
```
user calls: agent.invoke("ask_question", question="...", response_mode="concise|internal|verbose")
    ↓
retrieve_context_tool.invoke()
    ├─→ Generate question embedding (LLM)
    └─→ Semantic search in VectorDB
    ↓
rerank_context_tool.invoke()
    └─→ LLM re-evaluates relevance
    ↓
[Decision] Should optimize?
    ├─ If yes: get_context_cost_tool + optimize_chunk_size_tool
    └─ If no: continue
    ↓
answer_question_tool.invoke()
    └─→ LLM synthesizes answer from context
    ↓
traceability_tool.invoke()
    └─→ Create audit trail
    ↓
Apply Guardrails (based on response_mode)
    ├─ concise: hallucination_check + security_incident_policy
    ├─ internal: hallucination_check
    └─ verbose: no validation
    ↓
return: {answer, metadata, errors}
```

---

## Troubleshooting

### Issue: Database Not Found
```
[!] Database not found at src/incident_iq/database/data/incident_iq.db
```
**Solution:**
1. Check database path in `env_config.py`
2. Ensure database exists and contains `knowledge_base` table
3. Run database migrations if needed

### Issue: Empty Results
```
Retrieved 0 documents (quality score: 0.00)
```
**Solution:**
1. Verify table ingestion completed successfully
2. Check if vectordb has embeddings
3. Try simpler questions first

### Issue: Guardrails Not Available
```
[WARNING] Guardrails not installed. Install with: pip install guardrails-ai
```
**Solution:**
```bash
pip install guardrails-ai
```

### Issue: Tool Execution Errors
```
[✗] Error during table ingestion: ...
```
**Solution:**
1. Check console error messages
2. Verify all dependencies installed
3. Check LLM service connectivity
4. Review error traceback

---

## Expected Console Output

### Successful Ingestion
```
[STEP 2] Ingest SQLite Table (knowledge_base)
Configuration from data_sources.json:
  table_name: knowledge_base
  text_columns: ['cause', 'description', 'impact', 'remediation_steps', 'rca']
  metadata_columns: ['id', 'resource_type', 'environment', 'dollar_impact']

Result:
{
  "success": true,
  "table_name": "knowledge_base",
  "records_processed": 42,
  "total_chunks_saved": 150,
  "rbac_namespace": "general"
}

✓ Successfully ingested table
  Records processed: 42
  Total chunks saved: 150
```

### Successful Question Answering
```
[STEP 3] Ask Question - CONCISE Mode
Mode: concise (user-friendly)
Guardrails: hallucination_check + security_incident_policy

Question: What are the main incident causes?

Response:
  Success: true
  Answer: The main incident causes include network failures (45%), 
          configuration errors (30%), and security incidents (25%)...
  Session ID: 550e8400-e29b-41d4-a716-446655440000
  Guardrails Applied: true
```

---

## Next Steps After Testing

1. **Review Results:** Check if answers are accurate and relevant
2. **Verify Guardrails:** Confirm responses are validated appropriately
3. **Check Debug Output:** Ensure verbose mode shows tool execution
4. **Test Real Questions:** Ask domain-specific questions
5. **Performance Analysis:** Monitor execution times
6. **Error Handling:** Test error scenarios

---

## Reference Documentation

See these files for detailed information:
- `AGENT_TOOL_REFERENCE.md` - Complete tool reference guide
- `TOOL_DECISION_TREE.md` - Tool decision logic and sequences
- `AGENT_SYSTEM_PROMPTS.md` - Response modes and system prompts
- `REFACTORING_SUMMARY.md` - Code changes and improvements

---

## Support

For issues or questions:
1. Check the documentation files listed above
2. Review test output for error messages
3. Check application logs in `logs/` directory
4. Enable verbose mode for debugging
