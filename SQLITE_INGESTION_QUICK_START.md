# LangGraph SQLite Ingestion - Copy-Paste Guide

## 🚀 Quick Start

### Run the Ingestion Script
```bash
cd E:\ai-projects\incident_manangement
python invoke_langgraph_sqlite.py
```

### Run with Query
```bash
python invoke_langgraph_sqlite.py --query
```

---

## 💻 Copy-Paste Code

### Minimal Ingestion (Python)
```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "src"))

from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.ingestion_tools import ingest_sqlite_table_tool
from incident_iq.config.env_config import EnvConfig

agent = LangGraphRAGAgent()
result = ingest_sqlite_table_tool.invoke({
    "table_name": "knowledge_base",
    "doc_id": "sqlite_knowledge_base",
    "rbac_namespace": "general",
    "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
    "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"],
    "db_path": EnvConfig.get_db_path(),
    "llm_service": agent.llm_service,
    "vectordb_service": agent.vectordb_service,
    "chunk_size": 512,
    "chunk_overlap": 50
})
print(f"Success: {result}")
```

### Ingest + Query (Python)
```python
from pathlib import Path
import sys, json
sys.path.insert(0, str(Path.cwd() / "src"))

from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.ingestion_tools import ingest_sqlite_table_tool
from incident_iq.config.env_config import EnvConfig

# Ingest
agent = LangGraphRAGAgent()
result = ingest_sqlite_table_tool.invoke({
    "table_name": "knowledge_base",
    "doc_id": "sqlite_kb",
    "rbac_namespace": "general",
    "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
    "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"],
    "db_path": EnvConfig.get_db_path(),
    "llm_service": agent.llm_service,
    "vectordb_service": agent.vectordb_service,
    "chunk_size": 512,
    "chunk_overlap": 50
})

# Query
if json.loads(result if isinstance(result, str) else str(result)).get('success'):
    q = agent.ask_question("What are common incident causes?", response_mode="concise")
    print(q['answer'])
```

### Query After Ingestion (Python)
```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "src"))

from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Ask question
result = agent.ask_question(
    question="What should we do to remediate critical incidents?",
    response_mode="verbose"  # or "concise" for simple answer
)

print(f"Answer: {result['answer']}")
print(f"Quality: {result['retrieval_quality']:.1%}")
print(f"Sources: {result['sources_count']}")
print(f"Session: {result['session_id']}")
```

---

## 📊 Configuration Reference

### From data_sources.json
```json
{
  "table_name": "knowledge_base",
  "text_columns": [
    "cause",
    "description", 
    "impact",
    "remediation_steps",
    "rca"
  ],
  "metadata_columns": [
    "id",
    "resource_type",
    "environment",
    "dollar_impact"
  ],
  "chunk_size": 512,
  "chunk_overlap": 50
}
```

---

## 🔍 Expected Output

### Ingestion Success
```
🤖 LANGGRAPH MASTER AGENT - SQLITE TABLE INGESTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Configuration from: src/incident_iq/rag/config/data_sources.json
📊 Table: knowledge_base
📝 Text Columns: cause, description, impact, remediation_steps, rca
📎 Metadata: id, resource_type, environment, dollar_impact

✅ Ingestion Status: SUCCESS
📊 Chunks Saved: 247
🏷️  Doc ID: sqlite_knowledge_base_ingestion
🔐 RBAC Namespace: general
```

### Query Success
```
❓ Question: What are the common causes of incidents?

✅ Status: Success
📊 Retrieval Quality: 85%
📚 Sources Found: 5
⏱️  Execution Time: 1234.5ms

📝 Answer:
Common incident causes include: network failures, database 
connection issues, deployment errors, resource exhaustion, 
and configuration mismatches...

📖 Sources Retrieved:
   1. sqlite_knowledge_base_ingestion
   2. [source 2]
   3. [source 3]
```

---

## 📁 File Locations

| File | Purpose |
|------|---------|
| `invoke_langgraph_sqlite.py` | One-line invocation script |
| `test_langgraph_sqlite_pdf_ingestion.py` | Full test suite (SQLite + PDF) |
| `src/incident_iq/rag/config/data_sources.json` | Configuration |
| `src/incident_iq/rag/agents/langgraph_agent/langgraph_rag_agent.py` | Master agent |
| `src/incident_iq/rag/tools/ingestion_tools.py` | Ingestion tools |

---

## ⚙️ Services Used

### 1. LangGraph Agent
- Orchestrates workflows
- Manages state graphs
- Coordinates ingestion/retrieval

### 2. LLM Service
- Generates embeddings from text
- Uses configured LLM provider (Ollama, etc.)

### 3. VectorDB Service
- Stores embeddings in Chroma
- Performs similarity search
- Manages collections and namespaces

### 4. SQLite Database
- Source of data (knowledge_base table)
- Metadata tracking tables
- History and optimization records

---

## 🎯 Common Tasks

### Task 1: Ingest knowledge_base table
```bash
python invoke_langgraph_sqlite.py
```

### Task 2: Ingest and immediately query
```bash
python invoke_langgraph_sqlite.py --query
```

### Task 3: Custom table ingestion
Edit `invoke_langgraph_sqlite.py` line with table name:
```python
"table_name": "your_table_name",  # Change this
```

### Task 4: Verify ingestion
```python
# Check chunks in vectordb
agent.vectordb_service.collection.get(
    where={"doc_id": "sqlite_knowledge_base_ingestion"}
)
```

### Task 5: Query with traceability
```python
result = agent.ask_question(
    "Your question here?",
    response_mode="verbose"  # Full metadata
)
```

---

## 🐛 Troubleshooting

### Issue: "No records found in table 'knowledge_base'"
**Solution**: Check if table exists and has data
```bash
sqlite3 src/incident_iq/database/data/incident_iq.db
sqlite> SELECT COUNT(*) FROM knowledge_base;
sqlite> PRAGMA table_info(knowledge_base);
```

### Issue: "Failed to generate embedding"
**Solution**: Ensure LLM service is configured and running
```python
agent.llm_service.provider  # Check provider
agent.llm_service.model  # Check model
```

### Issue: "VectorDB save failed"
**Solution**: Check Chroma database permissions
```python
agent.vectordb_service.persist_directory  # Check path
```

---

## 📚 Documentation

- **Design Book**: `docs/LangGraph_DeepAgents_Design_Book.md`
- **SQLite Test**: `docs/LANGGRAPH_SQLITE_PDF_TEST.md`
- **Configuration**: `src/incident_iq/rag/config/data_sources.json`
- **Update Summary**: `LANGGRAPH_SQLITE_UPDATE.md`

