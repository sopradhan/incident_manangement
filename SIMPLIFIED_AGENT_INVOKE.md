# LangGraph Master Agent - Simplified One-Line Invocation

## 🎯 The Simplified Approach

Instead of manually calling the tool with all parameters, you now just call `agent.invoke()`:

### Before (Complex)
```python
agent = LangGraphRAGAgent()
result = ingest_sqlite_table_tool.invoke({
    "table_name": "knowledge_base",
    "doc_id": "sqlite_knowledge_base",
    "rbac_namespace": "general",
    "text_columns": [...],
    "metadata_columns": [...],
    "db_path": EnvConfig.get_db_path(),
    "llm_service": agent.llm_service,
    "vectordb_service": agent.vectordb_service,
    "chunk_size": 512,
    "chunk_overlap": 50
})
```

### After (Simple)
```python
agent = LangGraphRAGAgent()
result = agent.invoke("ingest_sqlite_table", table_name="knowledge_base")
```

**That's it!** The agent handles everything behind the scenes.

---

## 📋 Quick Start

### 1. Just Ingest
```bash
python invoke_langgraph_sqlite.py
```

### 2. Ingest and Query
```bash
python invoke_langgraph_sqlite.py --query
```

### 3. Show Examples
```bash
python invoke_langgraph_sqlite.py --help
```

---

## 🐍 Python API

### Ingest SQLite Table
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()
result = agent.invoke("ingest_sqlite_table", table_name="knowledge_base")

print(f"Success: {result['success']}")
print(f"Chunks: {result['chunks_saved']}")
```

### Ask Question
```python
result = agent.invoke("ask_question", question="What are common causes?")
print(result['answer'])
```

### Ingest Document
```python
result = agent.invoke("ingest_document", text="Your text here", doc_id="doc_001")
print(f"Chunks saved: {result['chunks_saved']}")
```

### Optimize System
```python
result = agent.invoke("optimize", 
                     performance_history=[...],
                     config_updates={...})
print(f"Optimization: {result['optimization']}")
```

---

## 🏗️ What Happens Behind the Scenes

When you call:
```python
agent.invoke("ingest_sqlite_table", table_name="knowledge_base")
```

The agent automatically:

1. **Loads Configuration**: Reads `data_sources.json`
2. **Extracts Table Config**: Gets columns, chunking settings
3. **Connects to Database**: Opens `incident_iq.db`
4. **Fetches Records**: Gets all records from `knowledge_base`
5. **Converts to Text**: Structures data for embedding
6. **Chunks Content**: Splits into 512-char pieces (50 overlap)
7. **Generates Embeddings**: Creates vectors from text
8. **Stores in VectorDB**: Saves to Chroma database
9. **Tracks Metadata**: Logs ingestion details
10. **Returns Result**: Success/failure with statistics

All with one line of code!

---

## 📊 Agent Operations

| Operation | Call | Parameters | Returns |
|-----------|------|------------|---------|
| **Ingest Table** | `"ingest_sqlite_table"` | `table_name` | `success`, `chunks_saved` |
| **Ingest Doc** | `"ingest_document"` | `text`, `doc_id` | `success`, `chunks_count` |
| **Ask Question** | `"ask_question"` | `question`, `response_mode` | `answer`, `sources`, `quality` |
| **Optimize** | `"optimize"` | `performance_history`, `config_updates` | `optimization`, `config_result` |

---

## 💡 Real-World Usage

### Use Case 1: ETL Pipeline
```python
agent = LangGraphRAGAgent()

# Ingest multiple tables
tables = ["knowledge_base", "incidents", "runbooks"]
for table in tables:
    result = agent.invoke("ingest_sqlite_table", table_name=table)
    print(f"Ingested {table}: {result['chunks_saved']} chunks")
```

### Use Case 2: RAG Chatbot
```python
agent = LangGraphRAGAgent()

# First time: ingest data
agent.invoke("ingest_sqlite_table", table_name="knowledge_base")

# Then: answer user questions
while True:
    question = input("Q: ")
    result = agent.invoke("ask_question", question=question)
    print(f"A: {result['answer']}")
```

### Use Case 3: Batch Processing
```python
agent = LangGraphRAGAgent()

documents = [
    ("doc1", "Content of document 1"),
    ("doc2", "Content of document 2"),
]

for doc_id, content in documents:
    result = agent.invoke("ingest_document", text=content, doc_id=doc_id)
    if result['success']:
        print(f"✅ Ingested {doc_id}")
    else:
        print(f"❌ Failed to ingest {doc_id}")
```

---

## 🚀 Execution Options

### Option 1: Command Line (Simplest)
```bash
python invoke_langgraph_sqlite.py              # Ingest only
python invoke_langgraph_sqlite.py --query      # Ingest + query
```

### Option 2: Python Script
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()
result = agent.invoke("ingest_sqlite_table", table_name="knowledge_base")
```

### Option 3: Interactive Python
```python
>>> from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
>>> agent = LangGraphRAGAgent()
>>> agent.invoke("ingest_sqlite_table", table_name="knowledge_base")
{'success': True, 'chunks_saved': 247, 'doc_id': 'sqlite_knowledge_base', ...}
```

---

## 📁 Files Updated

| File | Changes |
|------|---------|
| `src/.../langgraph_rag_agent.py` | Added `invoke()` method |
| `invoke_langgraph_sqlite.py` | Simplified to use `agent.invoke()` |

---

## ✅ Key Advantages

✨ **Simplicity**: One-line invocation for all operations
✨ **Automation**: Configuration loaded automatically
✨ **Consistency**: Same interface for all operations
✨ **Scalability**: Easy to add more operations
✨ **Readability**: Clear what operation is being performed
✨ **Flexibility**: Optional parameters for customization

---

## 📝 Example Outputs

### Ingestion Success
```
🤖 LANGGRAPH MASTER AGENT - SQLITE TABLE INGESTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Status: SUCCESS
📊 Chunks Saved: 247
🏷️  Doc ID: sqlite_knowledge_base
```

### Query Success
```
Q: What are common causes of incidents?
A: Common incident causes include network failures (35%), 
   database connection issues (28%), deployment errors (18%), 
   resource exhaustion (12%), and configuration mismatches (7%)...
```

---

## 🎓 Next Steps

1. Run: `python invoke_langgraph_sqlite.py`
2. Try: `python invoke_langgraph_sqlite.py --query`
3. Integrate: Use `agent.invoke()` in your code
4. Customize: Add more tables to `data_sources.json`
5. Monitor: Check logs for RL healing agent optimizations

