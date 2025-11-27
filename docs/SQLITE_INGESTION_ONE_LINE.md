# LangGraph Master Agent - SQLite Ingestion One-Line Invocation

## Quick Reference

### The One-Liner
```python
# Load config from data_sources.json and invoke
agent = LangGraphRAGAgent()
result = ingest_sqlite_table_tool.invoke({
    "table_name": "knowledge_base",
    "doc_id": "sqlite_knowledge_base_ingestion",
    "rbac_namespace": "general",
    "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
    "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"],
    "db_path": EnvConfig.get_db_path(),
    "llm_service": agent.llm_service,
    "vectordb_service": agent.vectordb_service,
    "chunk_size": 512,
    "chunk_overlap": 50
})
```

---

## Configuration Source

**File**: `src/incident_iq/rag/config/data_sources.json`

**Current Configuration for knowledge_base**:
```json
{
  "name": "knowledge_base",
  "enabled": true,
  "description": "Main incident knowledge base",
  "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
  "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"],
  "chunk_strategy": "per_record"
}
```

**Chunking Settings**:
```json
{
  "enabled": true,
  "strategy": "semantic",
  "chunk_size": 512,
  "overlap": 50
}
```

---

## Execution Options

### Option 1: Run Direct Script
```bash
python invoke_langgraph_sqlite.py
```

**Output**:
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

### Option 2: Ingest and Query
```bash
python invoke_langgraph_sqlite.py --query
```

**Flow**:
1. Ingest knowledge_base table
2. Wait for vectorization
3. Query with 3 example questions
4. Display results with source attribution

### Option 3: Interactive Python
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
    "doc_id": "sqlite_knowledge_base_ingestion",
    "rbac_namespace": "general",
    "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
    "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"],
    "db_path": EnvConfig.get_db_path(),
    "llm_service": agent.llm_service,
    "vectordb_service": agent.vectordb_service,
    "chunk_size": 512,
    "chunk_overlap": 50
})
```

---

## Component Breakdown

### 1. Master Agent Initialization
```python
agent = LangGraphRAGAgent()
```
Initializes the LangGraph master orchestrator with:
- LLM Service (for embeddings)
- VectorDB Service (Chroma)
- Config Service (for system settings)
- RL Healing Agent (for optimization)

### 2. Tool Invocation
```python
ingest_sqlite_table_tool.invoke({...})
```
Invokes the orchestrator through the ingestion tool with full context:
- **table_name**: SQLite table to ingest
- **doc_id**: Unique document identifier for tracking
- **rbac_namespace**: RBAC security domain
- **text_columns**: Columns to combine for searchable content
- **metadata_columns**: Columns to extract as metadata
- **db_path**: Database path
- **Services**: LLM and VectorDB service instances
- **Chunking**: Size and overlap parameters

### 3. Configuration from data_sources.json
The tool respects the configuration:
```
data_sources.json
└── sqlite (enabled: true)
    ├── table_based
    │   └── knowledge_base
    │       ├── text_columns: [cause, description, impact, ...]
    │       ├── metadata_columns: [id, resource_type, environment, ...]
    │       └── chunk_strategy: per_record
    └── chunking
        ├── chunk_size: 512
        └── overlap: 50
```

---

## What Happens Inside

### Ingestion Pipeline
```
┌─────────────────────────────────────────────────┐
│ 1. CONNECT to SQLite Database                   │
│    └─ Load: incident_iq.db                      │
├─────────────────────────────────────────────────┤
│ 2. FETCH Records from knowledge_base table      │
│    └─ WHERE: all enabled records                │
├─────────────────────────────────────────────────┤
│ 3. EXTRACT Text & Metadata per record           │
│    ├─ Text: cause + description + impact + ...  │
│    └─ Meta: id, resource_type, environment ...  │
├─────────────────────────────────────────────────┤
│ 4. CHUNK each record (512 chars, 50 overlap)    │
│    └─ Strategy: Semantic/Recursive splitter     │
├─────────────────────────────────────────────────┤
│ 5. EMBED each chunk                             │
│    └─ Model: Configured LLM provider            │
├─────────────────────────────────────────────────┤
│ 6. STORE in Chroma VectorDB                     │
│    ├─ Collection: rag_embeddings                │
│    ├─ Namespace: general (RBAC)                 │
│    └─ Metadata: doc_id, chunk_id, ...           │
├─────────────────────────────────────────────────┤
│ 7. TRACK in SQLite (metadata tables)            │
│    └─ Tables: document_metadata, chunk_data     │
└─────────────────────────────────────────────────┘
```

### Data Flow
```
SQLite (Source)
    ↓
Rows → Text Conversion
    ↓
Chunking (semantic splitting)
    ↓
Embedding Generation (LLM)
    ↓
Chroma VectorDB (storage)
    ↓
Metadata Tracking (SQLite)
```

---

## Return Format

### Success Response
```json
{
  "success": true,
  "doc_id": "sqlite_knowledge_base_ingestion",
  "chunks_saved": 247,
  "rbac_namespace": "general"
}
```

### Error Response
```json
{
  "success": false,
  "error": "No records found in table 'knowledge_base'"
}
```

---

## After Ingestion

### Query the Ingested Data
```python
# Ask questions about the ingested knowledge base
result = agent.ask_question(
    "What are common incident causes?",
    response_mode="verbose"
)

print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources_count']}")
print(f"Quality: {result['retrieval_quality']:.1%}")
```

### Monitor Ingestion
```python
# Check database for ingested records
from incident_iq.database.models import DocumentMetadataModel

model = DocumentMetadataModel(db_path)
doc_record = model.get_by_id("sqlite_knowledge_base_ingestion")
print(f"Ingestion time: {doc_record['ingestion_date']}")
print(f"Chunks: {doc_record['chunks_saved']}")
```

---

## Key Points

✅ **Already Enabled**: SQLite ingestion is enabled in data_sources.json

✅ **Config-Driven**: Uses data_sources.json for all parameters

✅ **One-Line**: Single `ingest_sqlite_table_tool.invoke()` call

✅ **Orchestrated**: Goes through LangGraph master agent

✅ **Tracked**: Stores metadata for auditing and retrieval

✅ **Scalable**: Easy to add more tables to data_sources.json

---

## File Location

- **Invocation Script**: `invoke_langgraph_sqlite.py`
- **Configuration**: `src/incident_iq/rag/config/data_sources.json`
- **Test Script**: `test_langgraph_sqlite_pdf_ingestion.py`

