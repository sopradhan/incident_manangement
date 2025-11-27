# 🚀 LangGraph Agent - Quick Reference Card

## One-Liner Invocation

```python
agent = LangGraphRAGAgent()
result = agent.invoke("ingest_sqlite_table", table_name="knowledge_base")
```

That's it! No need to manually pass services, configs, or parameters.

---

## All Operations

### 1️⃣ Ingest SQLite Table
```python
result = agent.invoke("ingest_sqlite_table", table_name="knowledge_base")
```

**Returns**: `{'success': bool, 'chunks_saved': int, 'doc_id': str, ...}`

### 2️⃣ Ingest Document
```python
result = agent.invoke("ingest_document", text="Your text", doc_id="doc_001")
```

**Returns**: `{'success': bool, 'chunks_count': int, 'chunks_saved': int, ...}`

### 3️⃣ Ask Question
```python
result = agent.invoke("ask_question", question="What is X?")
```

**Returns**: `{'answer': str, 'sources': list, 'quality': float, ...}`

### 4️⃣ Optimize System
```python
result = agent.invoke("optimize", performance_history=[...], config_updates={...})
```

**Returns**: `{'optimization': dict, 'config_applied': dict, ...}`

---

## Command Line Usage

```bash
# Just ingest
python invoke_langgraph_sqlite.py

# Ingest and query
python invoke_langgraph_sqlite.py --query

# Show help
python invoke_langgraph_sqlite.py --help
```

---

## Configuration

Automatically loaded from: `src/incident_iq/rag/config/data_sources.json`

```json
{
  "name": "knowledge_base",
  "text_columns": ["cause", "description", "impact", ...],
  "metadata_columns": ["id", "resource_type", "environment", ...],
  "chunk_size": 512,
  "overlap": 50
}
```

---

## What Happens Automatically

✅ Load configuration from `data_sources.json`
✅ Extract table metadata (columns, chunking)
✅ Connect to SQLite database
✅ Fetch records and convert to text
✅ Chunk content
✅ Generate embeddings
✅ Store in Chroma VectorDB
✅ Track metadata
✅ Return results

All in one call! 🎉

---

## Complete Working Example

```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

# Initialize agent
agent = LangGraphRAGAgent()

# 1. Ingest SQLite table
print("Ingesting knowledge_base...")
ingest_result = agent.invoke("ingest_sqlite_table", table_name="knowledge_base")
print(f"✅ Chunks saved: {ingest_result['chunks_saved']}")

# 2. Ask questions
print("\nAsking questions...")
q_result = agent.invoke("ask_question", question="What are incident causes?")
print(f"Answer: {q_result['answer'][:200]}...")

# 3. Get detailed traceability
verbose_result = agent.invoke("ask_question", 
                              question="What are incident causes?",
                              response_mode="verbose")
print(f"Sources: {verbose_result['sources_count']}")
print(f"Quality: {verbose_result['retrieval_quality']:.1%}")
```

---

## Response Modes

```python
# Concise (default) - just answer
agent.invoke("ask_question", question="?", response_mode="concise")

# Verbose - full metadata and traceability  
agent.invoke("ask_question", question="?", response_mode="verbose")

# Internal - structured data for system updates
agent.invoke("ask_question", question="?", response_mode="internal")
```

---

## Error Handling

```python
result = agent.invoke("ingest_sqlite_table", table_name="knowledge_base")

if result.get('success'):
    print(f"✅ Success: {result['chunks_saved']} chunks")
else:
    print(f"❌ Error: {result.get('error')}")
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `No records found` | Check table exists and has data |
| `Failed to generate embedding` | Check LLM service is running |
| `VectorDB save failed` | Check Chroma database permissions |
| `Unknown operation` | Check operation name is valid |

---

## Files

| File | Purpose |
|------|---------|
| `invoke_langgraph_sqlite.py` | Command-line script |
| `src/.../langgraph_rag_agent.py` | Agent with `invoke()` method |
| `src/.../config/data_sources.json` | Configuration file |

---

## Summary

**Before**: 12 lines of code with manual parameter passing
**After**: 1 line of code with automatic configuration

```python
# Before
agent = LangGraphRAGAgent()
result = ingest_sqlite_table_tool.invoke({
    "table_name": "knowledge_base",
    "doc_id": "sqlite_knowledge_base",
    "rbac_namespace": "general",
    "text_columns": [...],  # Manual
    "metadata_columns": [...],  # Manual
    "db_path": ...,  # Manual
    "llm_service": agent.llm_service,  # Manual
    "vectordb_service": agent.vectordb_service,  # Manual
    "chunk_size": 512,  # Manual
    "chunk_overlap": 50  # Manual
})

# After
agent = LangGraphRAGAgent()
result = agent.invoke("ingest_sqlite_table", table_name="knowledge_base")
```

🎉 **Done!**

