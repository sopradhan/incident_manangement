# LangGraph Agent - SQLite & PDF Ingestion Test

## Test File Location
`test_langgraph_sqlite_pdf_ingestion.py`

## What's New

### 1. Data Sources Configuration Integration
- **Imports**: Now imports `ingest_sqlite_table_tool` and loads `data_sources.json` config
- **Config Loading**: `load_data_sources_config()` function reads the data sources JSON
- **Table Extraction**: `get_table_config_from_data_sources()` extracts specific table configurations

### 2. SQLite Table Ingestion via Orchestrator
The test now properly invokes the master LangGraph agent through the orchestrator pattern:

**Process Flow**:
1. Load `data_sources.json` configuration from `src/incident_iq/rag/config/data_sources.json`
2. Extract table metadata from configuration:
   - `text_columns`: Columns to combine for searchable text
   - `metadata_columns`: Columns to attach as metadata
   - `chunk_size`: Configurable chunking size (default: 512)
   - `chunk_overlap`: Overlap between chunks (default: 50)
3. Initialize `LangGraphRAGAgent` (master agent)
4. Invoke `ingest_sqlite_table_tool` with:
   - Table name from database
   - Document ID
   - RBAC namespace
   - Text and metadata columns from config
   - Services (LLM + VectorDB) from agent
5. Store results in Chroma vector database

**Key Features**:
- Reads configuration from `data_sources.json` for consistency
- Uses intelligent column selection based on config
- Applies chunking strategy defined in config
- Tracks ingestion with doc_id and RBAC namespace
- Logs metadata to SQLite for tracking

### 3. PDF Document Ingestion
Maintains PDF ingestion capability with:
- Sample PDF generation using ReportLab
- PDF text extraction using PyPDF2/pypdf
- Fallback to sample content if PDF libraries not available
- Ingestion through LangGraph agent's document ingestion pipeline

### 4. Retrieval Tests
Tests query across both ingested sources:
- **Concise Mode**: End-user friendly responses
- **Verbose Mode**: Full traceability with metadata and RL healing info
- **Internal Mode**: Structured data for system updates

---

## Running the Test

```bash
# Basic run
python test_langgraph_sqlite_pdf_ingestion.py

# With verbose output
python -u test_langgraph_sqlite_pdf_ingestion.py
```

### Prerequisites
```bash
# Required (usually installed)
pip install langgraph langchain chroma-db

# Optional for PDF support
pip install reportlab pypdf
```

---

## Test Output Structure

```
🤖 LANGGRAPH MASTER AGENT - SQLITE & PDF INGESTION TESTS
├── 📋 1. SQLite Table Ingestion (via Orchestrator with data_sources.json)
│   ├── ✅ Loaded data_sources.json configuration
│   ├── ✅ Initialized LangGraphRAGAgent
│   ├── 📂 Database: [path]
│   ├── 📊 Available tables: [list]
│   ├── 📥 Selected table: [table_name]
│   ├── 📋 Text columns: [columns]
│   ├── 📎 Metadata columns: [columns]
│   └── ✅ Ingestion Result
│
├── 📋 2. PDF Document Ingestion
│   ├── 📝 Creating sample PDF
│   ├── ✅ PDF created successfully
│   └── ✅ Ingestion Result
│
├── 📋 3. Retrieval from Ingested Sources
│   ├── ❓ Question 1
│   ├── ❓ Question 2
│   └── ...
│
└── 📋 4. Verbose Retrieval with Traceability
    ├── 📝 Answer with full metadata
    ├── 🔧 Optimization details
    └── 📖 Source documents
```

---

## Configuration Reference

### data_sources.json Structure
```json
{
  "data_sources": {
    "sqlite": {
      "enabled": true,
      "ingestion_modes": {
        "table_based": {
          "tables_to_ingest": [
            {
              "name": "table_name",
              "enabled": true,
              "text_columns": ["col1", "col2"],
              "metadata_columns": ["col3", "col4"]
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

---

## Test Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Master LangGraph Agent                                      │
│                                                             │
│  1. SQLITE TABLE INGESTION                                  │
│     ├─ Load data_sources.json config                        │
│     ├─ Get table config (text/metadata columns)             │
│     ├─ Call ingest_sqlite_table_tool                        │
│     ├─ Generate embeddings via LLMService                   │
│     └─ Save to Chroma VectorDB                              │
│                                                             │
│  2. PDF INGESTION                                           │
│     ├─ Create/Load PDF document                             │
│     ├─ Extract text content                                 │
│     ├─ Call LangGraph ingest_document pipeline              │
│     ├─ Generate embeddings                                  │
│     └─ Save to Chroma VectorDB                              │
│                                                             │
│  3. RETRIEVAL (with RL Healing)                             │
│     ├─ Accept user question                                 │
│     ├─ Retrieve context from VectorDB                       │
│     ├─ Rerank by relevance                                  │
│     ├─ Check with RL Healing Agent for optimization         │
│     ├─ Generate answer                                      │
│     └─ Return with traceability                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         ↓                 ↓                 ↓
     SQLite DB      Chroma VectorDB     RL History
```

---

## Key Differences from Previous Version

| Aspect | Old | New |
|--------|-----|-----|
| **Config Source** | Hardcoded column lists | `data_sources.json` |
| **Orchestration** | Direct text conversion | `ingest_sqlite_table_tool` invocation |
| **Table Config** | No configuration | Loaded from `data_sources.json` |
| **Agent Type** | Text-based ingestion | Master LangGraph agent coordination |
| **Chunking Strategy** | Hardcoded | Configurable via `data_sources.json` |
| **RBAC Support** | Basic | Enhanced with namespace from config |

---

## Next Steps

1. **Run the test**: `python test_langgraph_sqlite_pdf_ingestion.py`
2. **Verify ingestion**: Check Chroma vector database for stored embeddings
3. **Test queries**: Ask questions about the ingested data
4. **Monitor logs**: Check for healing agent optimization decisions
5. **Analyze metadata**: Review ingestion statistics and traceability

