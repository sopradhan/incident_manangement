# Update Summary: LangGraph SQLite Table Ingestion via Orchestrator

## Overview
Updated `test_langgraph_sqlite_pdf_ingestion.py` to properly invoke the master LangGraph agent with data source orchestration pattern using `data_sources.json` configuration.

## Changes Made

### 1. **Imports Updated**
- Added: `from incident_iq.rag.tools.ingestion_tools import ingest_sqlite_table_tool`
- Purpose: Direct access to the SQLite table ingestion tool

### 2. **New Helper Functions**

#### `load_data_sources_config(config_path: str = None) -> dict`
- Loads `data_sources.json` configuration
- Falls back to default path if not specified
- Returns parsed JSON config or empty dict on error

#### `get_table_config_from_data_sources(config: dict, table_name: str) -> dict`
- Extracts table-specific configuration from the data sources config
- Returns text_columns, metadata_columns, and other table settings
- Used for intelligent column selection during ingestion

### 3. **SQLite Ingestion Refactor**

**Old Approach**:
```python
# Convert entire table to text, then ingest as document
table_text = get_sqlite_table_as_text(db_path, table_to_ingest, limit=20)
result = agent.ingest_document(table_text, doc_id)
```

**New Approach**:
```python
# Load config, use ingest_sqlite_table_tool with orchestrator pattern
config = load_data_sources_config()
table_config = get_table_config_from_data_sources(config, table_to_ingest)
text_columns = table_config.get("text_columns", [])
metadata_columns = table_config.get("metadata_columns", [])

result_json = ingest_sqlite_table_tool.invoke({
    "table_name": table_to_ingest,
    "doc_id": doc_id,
    "rbac_namespace": rbac_namespace,
    "text_columns": text_columns,
    "metadata_columns": metadata_columns,
    "db_path": db_path,
    "llm_service": agent.llm_service,
    "vectordb_service": agent.vectordb_service,
    "chunk_size": chunk_size,
    "chunk_overlap": chunk_overlap
})
```

### 4. **Configuration-Driven Workflow**

The new approach uses the orchestrator pattern:
1. **Load Config**: `data_sources.json` defines table schemas
2. **Extract Config**: Get table-specific settings (columns, chunking)
3. **Invoke Tool**: Call `ingest_sqlite_table_tool` with full context
4. **Pass Services**: Use LangGraph agent's LLM and VectorDB services
5. **Store Results**: Embeddings saved to Chroma with RBAC namespace

### 5. **Enhanced Logging**
```
✅ Loaded data_sources.json configuration
✅ Initialized LangGraphRAGAgent
📂 Database: [path]
📊 Available tables: [table_list]
📥 Selected table: [table_name]
✅ Found table config in data_sources.json
📋 Text columns: [col1, col2, col3]
📎 Metadata columns: [col4, col5]
🔪 Chunk size: 512, overlap: 50
🔄 Invoking Master LangGraph Agent for table ingestion...
```

### 6. **Test Title and Header**
- Updated: "SQLite Table Ingestion" → "SQLite Table Ingestion (via Orchestrator with data_sources.json)"
- Clearer indication of orchestration pattern being tested

---

## Benefits of New Approach

| Aspect | Benefit |
|--------|---------|
| **Configurability** | Column selection defined in JSON, not hardcoded |
| **Reusability** | Same config works across different ingestion contexts |
| **Proper Tool Usage** | Uses `ingest_sqlite_table_tool` as designed |
| **Metadata Tracking** | Better metadata extraction from specific columns |
| **Scalability** | Easy to add more tables to `data_sources.json` |
| **Orchestration** | Follows master agent orchestration pattern |
| **RBAC Support** | Namespace support built in |

---

## Testing

Run the updated test:
```bash
python test_langgraph_sqlite_pdf_ingestion.py
```

Expected output shows:
1. Config loading from `data_sources.json`
2. Table configuration extraction
3. Orchestrator invocation with proper parameters
4. Chunking and embedding generation
5. VectorDB storage with metadata
6. Query retrieval from ingested data

---

## Files Modified

- `test_langgraph_sqlite_pdf_ingestion.py` - Main test file (updated)
- `docs/LANGGRAPH_SQLITE_PDF_TEST.md` - Documentation (created)
- `docs/LangGraph_DeepAgents_Design_Book.md` - Design reference (existing)

---

## Configuration Reference

The test now respects `src/incident_iq/rag/config/data_sources.json`:

```json
{
  "data_sources": {
    "sqlite": {
      "enabled": true,
      "ingestion_modes": {
        "table_based": {
          "tables_to_ingest": [
            {
              "name": "knowledge_base",
              "enabled": true,
              "text_columns": ["cause", "description", "impact"],
              "metadata_columns": ["id", "resource_type", "environment"]
            }
          ]
        }
      },
      "chunking": {
        "chunk_size": 512,
        "overlap": 50
      }
    }
  }
}
```

