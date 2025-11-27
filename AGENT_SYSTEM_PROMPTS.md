# Agent System Prompts & Tool Decision Guide

## 🎯 Quick Reference: When Each Tool Gets Invoked

### INGESTION WORKFLOW
**Triggered by:** `agent.invoke("ingest_document", text="...", doc_id="...")`

| Stage | Tool | Condition | Input | Output |
|-------|------|-----------|-------|--------|
| 1 | `extract_metadata_tool` | Always | text, llm_service | metadata dict |
| 2 | `chunk_document_tool` | Always | text, doc_id | list of chunks |
| 3 | `save_to_vectordb_tool` | Always | chunks, doc_id, services | chunks_saved count |
| 4 | `update_metadata_tracking_tool` | Always | doc_id, metadata, chunks_saved | success status |

### TABLE INGESTION
**Triggered by:** `agent.invoke("ingest_sqlite_table", table_name="...", text_columns=[...])`

| Stage | Tool | Condition |
|-------|------|-----------|
| All-in-one | `ingest_sqlite_table_tool` | Always |
| (Internally uses save_to_vectordb_tool for each row chunk) | ↓ | ↓ |

### FOLDER INGESTION
**Triggered by:** `agent.invoke("ingest_from_path", path="...", recursive=True)`

| Stage | Tool | Condition |
|-------|------|-----------|
| Discovery | `ingest_documents_from_path_tool` | Always |
| For Each File | `extract_metadata_tool` | For each discovered file |
| ↓ | `chunk_document_tool` | ↓ |
| ↓ | `save_to_vectordb_tool` | ↓ |
| ↓ | `update_metadata_tracking_tool` | ↓ |

### RETRIEVAL WORKFLOW
**Triggered by:** `agent.invoke("ask_question", question="...", response_mode="concise|internal|verbose")`

| Stage | Tool | Condition | Debug Output |
|-------|------|-----------|--------------|
| 1 | `retrieve_context_tool` | Always | verbose/internal: "Retrieved X docs" |
| 2 | `rerank_context_tool` | Always | verbose/internal: "Reranked with scores" |
| 3 | Optimization Check | If quality < 0.6 OR results < 3 | N/A |
| 3a | `get_context_cost_tool` | If optimize=True | Cost analysis |
| 3b | `optimize_chunk_size_tool` | If optimize=True | Suggestions logged |
| 4 | `answer_question_tool` | Always | verbose/internal: "Answer generated" |
| 5 | `traceability_tool` | Always | Creates audit trail |
| 6 | Guardrails Validation | Based on response_mode | concise/internal only |

### OPTIMIZATION WORKFLOW
**Triggered by:** `agent.invoke("optimize", performance_history=[...], config_updates={...})`

| Stage | Tool | Condition |
|-------|------|-----------|
| 1 | `optimize_chunk_size_tool` | Always |
| 2 | `adjust_config_tool` | Always |

---

## 📊 Tool Decision Matrix: When to Use What?

```
┌─ Need to ingest content?
│  ├─ Raw text string? → use extract_metadata_tool + chunk_document_tool + save_to_vectordb_tool
│  ├─ Database table? → use ingest_sqlite_table_tool (all-in-one)
│  └─ Folder of files? → use ingest_documents_from_path_tool (discovery) + above for each
│
├─ Need to answer question?
│  ├─ Retrieve context → retrieve_context_tool
│  ├─ Improve relevance → rerank_context_tool
│  ├─ Check if optimization needed?
│  │  ├─ YES: use get_context_cost_tool + optimize_chunk_size_tool
│  │  └─ NO: skip optimization
│  ├─ Generate answer → answer_question_tool
│  ├─ Create audit trail → traceability_tool
│  └─ Apply guardrails → based on response_mode
│
└─ Need to optimize system?
   ├─ Analyze performance → optimize_chunk_size_tool
   └─ Apply config changes → adjust_config_tool
```

---

## 🎬 System Prompts by Response Mode

### CONCISE MODE
**User:** End-user
**Output:** Clean answer only
**System Prompt (Implied):**
```
"Provide a concise, user-friendly answer to the question.
Focus on the key information without unnecessary details.
If uncertain, acknowledge the limitation.
Answer must be validated for:
  1. Hallucination check (accuracy)
  2. Security incident policy (safety & compliance)"
```

**Tools Used:**
- retrieve_context_tool (k=5)
- rerank_context_tool (filter low confidence)
- answer_question_tool (concise format)
- Guardrails: hallucination_check + security_incident_policy

### INTERNAL MODE
**User:** System/API consumer
**Output:** Clean answer + structured metadata
**System Prompt (Implied):**
```
"Provide a structured response suitable for API integration.
Include quality metrics and source attribution.
Format for database compatibility.
Validate for hallucination only - system handles security."
```

**Tools Used:**
- retrieve_context_tool (k=5)
- rerank_context_tool
- answer_question_tool
- Guardrails: hallucination_check only

### VERBOSE MODE
**User:** Engineer/Admin/Debugger
**Output:** Full business intelligence
**System Prompt (Implied):**
```
"Provide complete technical details for debugging and analysis.
Include all metadata, traceability, and RL recommendations.
Show optimization decisions and alternatives.
No guardrails - engineers need raw data for analysis."
```

**Tools Used:**
- retrieve_context_tool (k=5, detailed logging)
- rerank_context_tool (show all scores)
- answer_question_tool (with word count)
- traceability_tool (full lineage)
- Guardrails: NONE (raw data)
- RLHealingAgent recommendations shown
- Optimization details logged

---

## 🔄 Tool Invocation Sequence Diagrams

### Diagram 1: Ingestion Path
```
User Input (text, doc_id)
    │
    ├─→ extract_metadata_tool
    │   • LLM analyzes document
    │   • Outputs: title, summary, keywords, doc_type
    │   ↓
    ├─→ chunk_document_tool
    │   • RecursiveCharacterTextSplitter
    │   • Outputs: list of chunks with chunk_ids
    │   ↓
    ├─→ save_to_vectordb_tool
    │   • For each chunk: llm_service.generate_embedding()
    │   • Batch add to ChromaDB
    │   • Optional: save to SQLite
    │   • Outputs: chunks_saved count
    │   ↓
    ├─→ update_metadata_tracking_tool
    │   • Record audit trail
    │   • Mark as COMPLETED
    │   • Outputs: success status
    │   ↓
    └─→ User receives: {success, doc_id, chunks_saved, errors}
```

### Diagram 2: Retrieval Path
```
User Input (question, response_mode)
    │
    ├─→ retrieve_context_tool
    │   • llm_service.generate_embedding(question)
    │   • vectordb_service.search(embedding, k=5)
    │   • Outputs: top-5 chunks
    │   ↓
    ├─→ rerank_context_tool
    │   • LLM re-evaluates relevance
    │   • Reorder by score
    │   • Outputs: sorted chunks
    │   ↓
    ├─→ Check Optimization Needed?
    │   ├─ If quality < 0.6:
    │   │  ├─→ get_context_cost_tool (estimate tokens)
    │   │  └─→ optimize_chunk_size_tool (suggest params)
    │   └─ Continue
    │   ↓
    ├─→ answer_question_tool
    │   • LLM: synthesize answer from context
    │   • Format based on response_mode
    │   • Outputs: answer text
    │   ↓
    ├─→ traceability_tool
    │   • Create source attribution
    │   • Record chunk_ids and doc_ids
    │   • Outputs: traceability metadata
    │   ↓
    ├─→ Apply Guardrails (response_mode aware)
    │   ├─ concise: hallucination_check + security_incident_policy
    │   ├─ internal: hallucination_check only
    │   └─ verbose: no validation
    │   ↓
    └─→ User receives: answer + metadata (varies by mode)
```

### Diagram 3: Folder Ingestion Path
```
User Input (path, file_type, recursive)
    │
    ├─→ ingest_documents_from_path_tool
    │   • Scan path recursively (or not)
    │   • Filter by file_type
    │   • Generate doc_ids: {prefix}_{stem}_{timestamp}
    │   • Returns: list of {file_path, file_type, doc_id}
    │   ↓
    └─→ For each discovered document:
        │
        ├─→ extract_document_text_tool (optional)
        │   • PDF: pdfplumber or PyPDF2
        │   • TEXT: read file
        │   • DOCX: python-docx
        │   ↓
        ├─→ [Then run full ingestion pipeline above]
        │   • extract_metadata_tool
        │   • chunk_document_tool
        │   • save_to_vectordb_tool
        │   • update_metadata_tracking_tool
        │
        └─ Repeat for next file
    
    Final output: {documents_discovered, documents_ingested, documents_failed}
```

---

## 🛡️ Guardrails Validation Pipeline

### Concise Mode Guardrails
```
Input: Answer text

Step 1: Check for Hallucinations
  • Is the answer consistent with context?
  • Are facts grounded in sources?
  • Are inferences clearly marked?

Step 2: Apply Security Incident Policy
  • Does answer contain sensitive info?
  • Is answer policy-compliant?
  • Should answer be filtered/redacted?

Output: Validated answer or original if validation fails
```

### Internal Mode Guardrails
```
Input: Answer text

Step 1: Check for Hallucinations
  • Validate against source documents
  • Flag ungrounded statements
  
Skip: No security policy check (system handles security)

Output: Validated answer or original if validation fails
```

### Verbose Mode Guardrails
```
Input: Answer text

Step 1: No validation applied
  • Engineers need raw data for debugging
  • All information shown unfiltered
  
Output: Raw answer with all metadata
```

---

## 📋 Debug Output Triggers

### Concise Mode
- ✅ Minimal output (suppresses visualizations)
- ❌ No node-level logs
- ❌ No tool invocation details

### Internal Mode
- ✅ Node-level logs showing tool invocations
- ✅ Query/Reranking results logged
- ❌ Full source previews not shown
- ✅ Guardrails applied (hallucination check only)

### Verbose Mode
- ✅ Full debug output for every node
- ✅ Tool parameters and results shown
- ✅ Sample source document previews
- ✅ Relevance scores displayed
- ✅ RL recommendations shown
- ✅ Optimization decisions logged
- ❌ Guardrails disabled (raw data)
- ✅ Visualization saved to logs/

Example verbose output:
```
[🔍 RETRIEVE CONTEXT NODE - VERBOSE MODE]
  Question: What are the main incident risks?
  Retrieving top-k=5 relevant documents...
  ✓ Retrieved 5 documents (quality score: 1.00)
  [1] Doc: incident_2024_001 | The incident occurred on...
  [2] Doc: incident_2024_002 | Risk assessment shows...
  [3] Doc: incident_2024_003 | Impact analysis: ...

[📊 RERANK CONTEXT NODE - VERBOSE MODE]
  Reranking 5 documents for relevance...
  ✓ Reranked to 5 documents (sorted by relevance)
  [1] Score: 0.98 | Doc: incident_2024_001
  [2] Score: 0.95 | Doc: incident_2024_002
  [3] Score: 0.87 | Doc: incident_2024_003

[📋 ANSWER GENERATION NODE - VERBOSE MODE]
  Question: What are the main incident risks?
  Response Mode: verbose
  Reranked Context Items: 5
  ✓ Answer Generated (142 words)
  Answer Preview: The main incident risks identified include...
```

---

## 🚀 Usage Patterns

### Pattern 1: Batch Document Processing
```python
# Discover all PDFs in a folder
result = agent.invoke(
    "ingest_from_path",
    path="/data/incident_reports",
    file_type="pdf",
    doc_id_prefix="incident",
    recursive=True
)
# Returns: {documents_discovered: 100, documents_ingested: 99, errors: [...]}
```

### Pattern 2: Real-time Question Answering
```python
# Get quick user-facing answer
result = agent.invoke(
    "ask_question",
    question="What happened in the incident?",
    response_mode="concise"
)
# Returns: {success: true, answer: "...", guardrails_applied: true}
```

### Pattern 3: Integration with External Systems
```python
# Get structured response for API integration
result = agent.invoke(
    "ask_question",
    question="What are the action items?",
    response_mode="internal"
)
# Returns: {answer: "...", quality_score: 0.85, source_docs: [...]}
```

### Pattern 4: Engineering Analysis
```python
# Get full debug details
result = agent.invoke(
    "ask_question",
    question="Why didn't this resolve?",
    response_mode="verbose"
)
# Returns: {
#   answer: "...",
#   sources: [...],
#   traceability: {...},
#   rl_recommendation: {...},
#   optimization_result: {...},
#   visualization_data: {...}
# }
```

---

## ⚡ Performance Considerations

### Tool Execution Times (Approximate)
- `extract_metadata_tool`: 500ms (LLM call)
- `chunk_document_tool`: 50ms (text splitting)
- `save_to_vectordb_tool`: 2s (embedding generation + storage)
- `retrieve_context_tool`: 100ms (vector search)
- `rerank_context_tool`: 500ms (LLM re-ranking)
- `answer_question_tool`: 1s (LLM generation)
- `traceability_tool`: 50ms (data collection)

### Tool Resource Usage
- Memory Heavy: `save_to_vectordb_tool` (embeddings)
- CPU Intensive: `chunk_document_tool` (text processing)
- LLM Calls: `extract_metadata_tool`, `rerank_context_tool`, `answer_question_tool`
- I/O Bound: `retrieve_context_tool` (VectorDB query)

### Optimization Recommendations
- Use `response_mode="concise"` for high-frequency queries
- Batch folder ingestion with parallel processing (if supported)
- Pre-compute embeddings for static content
- Cache reranking results for repeated questions
