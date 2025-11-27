# Guardrails & Document Ingestion Integration - COMPLETE

## Overview
Successfully integrated Guardrails validation for response modes and consolidated all document ingestion (PDF, Text, Word) into a unified system with configuration-driven entry points.

## Key Achievements

### 1. ✅ Configuration-Driven Ingestion (data_sources.json)
- **PDF Support**: Enabled with chunk_size=1000, overlap=200, loader_type="pypdf"
- **Text Support**: Enabled with chunk_size=512, overlap=50, supported formats: .txt, .md, .markdown
- **Word Support**: Enabled with chunk_size=800, overlap=100, supported formats: .docx, .doc
- **Document Paths**: Auto-discovery with recursive scanning, symlink handling
- **Guardrails Policies**: Response-mode specific validation strategies

### 2. ✅ Consolidated Ingestion Tools (ingestion_tools.py)
All document ingestion functionality in one location:

#### Document Extraction Functions
- `extract_pdf_text_pdfplumber()` - PDF extraction with table support using pdfplumber
- `extract_pdf_text_pypdf()` - Fallback PDF extraction using PyPDF2
- `extract_text_file()` - Plain text and markdown file extraction
- `extract_word_file()` - Word document extraction with table support using python-docx
- `extract_document_text()` - Auto-detection wrapper for all file types

#### Discovery & Ingestion
- `ingest_documents_from_path_or_folder()` - Recursive document discovery
- `@tool ingest_documents_from_path_tool()` - Agent-callable tool with automatic doc_id generation

### 3. ✅ Guardrails Integration (langgraph_rag_agent.py)

#### Validation Strategy
- **Concise Mode (User)**: Full validation with `hallucination_check()` + `security_incident_policy()`
- **Internal Mode (System)**: Lightweight validation with `hallucination_check()` only
- **Verbose Mode (Engineer)**: No guardrails (raw data for debugging)

#### Implementation Details
- `_init_guardrails()` - Initializes three Guard instances per response mode
- `_apply_guardrails_validation()` - Validates responses before returning to user
- Applied in each response mode of `ask_question()` method
- Graceful fallback if Guardrails unavailable (HAS_GUARDRAILS flag)

### 4. ✅ Enhanced invoke() Method Operations

#### Existing Operations
- `invoke("ingest_document", text=..., doc_id=...)`
- `invoke("ingest_sqlite_table", table_name=..., doc_id=..., ...)`
- `invoke("ask_question", question=..., response_mode=...)`
- `invoke("optimize", performance_history=..., config_updates=...)`

#### New Operation
- `invoke("ingest_from_path", path=..., doc_id_prefix=..., file_type=..., recursive=...)`
  - Discovers documents from file path
  - Auto-generates doc_ids based on filename + timestamp
  - Ingests each discovered document
  - Returns detailed ingestion report with success metrics

### 5. ✅ System Prompt Verbosity

#### Conditional Debug Output
- **Concise Mode**: Minimal output (suppresses visualization logs)
- **Internal Mode**: Moderate output (shows tools being invoked, metrics)
- **Verbose Mode**: Full output (all metadata, traceability, tool details)

#### Enhanced Nodes
- `retrieve_context_node()` - Shows document count, quality score, top results
- `rerank_context_node()` - Shows reranking results with relevance scores
- `answer_question_node()` - Shows answer generation, database logging, metrics

## Usage Examples

### Example 1: Ingest Documents from Folder
```python
from src.incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Ingest all PDFs from docs folder recursively
result = agent.invoke("ingest_from_path", 
    path="./docs",
    doc_id_prefix="incident_doc",
    file_type="pdf",
    recursive=True
)

print(f"Discovered: {result['documents_discovered']}")
print(f"Ingested: {result['documents_ingested']}")
print(f"Failed: {result['documents_failed']}")
```

### Example 2: Query with Guardrails Validation
```python
# Concise mode with full guardrails (hallucination + security)
response = agent.ask_question(
    question="What are the critical incidents?",
    response_mode="concise"
)
print(f"Guardrails Applied: {response['guardrails_applied']}")
print(f"Answer: {response['answer']}")

# Internal mode with hallucination check only
response = agent.ask_question(
    question="What are the critical incidents?",
    response_mode="internal"
)
print(f"Quality Score: {response['quality_score']}")
print(f"Sources: {response['sources_count']}")

# Verbose mode with no guardrails (full metadata)
response = agent.ask_question(
    question="What are the critical incidents?",
    response_mode="verbose"
)
print(f"Traceability: {response['traceability']}")
print(f"RL Recommendation: {response['rl_recommendation']}")
```

### Example 3: Mixed Ingestion Pipeline
```python
# Step 1: Ingest from SQLite table
agent.invoke("ingest_sqlite_table",
    table_name="incidents",
    doc_id="sqlite_incidents_001"
)

# Step 2: Ingest text documents from folder
agent.invoke("ingest_from_path",
    path="./knowledge_base",
    doc_id_prefix="kb",
    file_type="text"
)

# Step 3: Query with proper response mode
response = agent.ask_question(
    question="How do we handle critical incidents?",
    response_mode="concise"
)
```

## Configuration Structure (data_sources.json)

```json
{
  "data_sources": {
    "pdf": {
      "enabled": true,
      "chunk_size": 1000,
      "overlap": 200,
      "loader_type": "pypdf"
    },
    "text": {
      "enabled": true,
      "supported": [".txt", ".md", ".markdown"],
      "chunk_size": 512,
      "overlap": 50
    },
    "word": {
      "enabled": true,
      "supported": [".docx", ".doc"],
      "chunk_size": 800,
      "overlap": 100
    }
  },
  "document_paths": {
    "enabled": true,
    "default_directories": ["./docs", "./knowledgebase"],
    "recursive": true,
    "follow_symlinks": false,
    "chunk_strategies": {
      "pdf": {"method": "semantic", "size": 1000},
      "text": {"method": "line_aware", "size": 512},
      "word": {"method": "paragraph_aware", "size": 800}
    }
  },
  "guardrails": {
    "response_mode_policies": {
      "concise": {
        "validators": ["hallucination_check", "security_incident_policy"],
        "description": "User-friendly with full validation"
      },
      "internal": {
        "validators": ["hallucination_check"],
        "description": "System integration with lightweight validation"
      },
      "verbose": {
        "validators": [],
        "description": "Engineer view with no guardrails"
      }
    }
  }
}
```

## Files Modified

### 1. `data_sources.json`
- Added PDF, text, word document configuration
- Added document_paths section for recursive discovery
- Added guardrails section with response mode policies

### 2. `ingestion_tools.py`
- Added 6 extraction functions (PDF, Text, Word)
- Added extract_document_text() auto-detection
- Added ingest_documents_from_path_or_folder() discovery
- Added @tool ingest_documents_from_path_tool() for agent

### 3. `langgraph_rag_agent.py`
- Added Guardrails imports (Guard, hallucination_check, security_incident_policy)
- Added _init_guardrails() method with 3 Guard instances
- Added _apply_guardrails_validation() method
- Updated ask_question() with guardrails validation per response mode
- Added "ingest_from_path" operation to invoke() method
- Enhanced node functions with conditional debug output (verbosity control)

## Response Mode Behaviors

### Concise Mode (User-Facing)
```
Response Format: { success, question, answer, session_id, guardrails_applied, errors }
Validation: hallucination_check + security_incident_policy
Output: Minimal (answer only, no metadata)
Debug: Suppressed visualization logs
```

### Internal Mode (System Integration)
```
Response Format: { success, answer, quality_score, sources_count, source_docs, metadata, guardrails_applied, errors }
Validation: hallucination_check only
Output: Structured data for database updates
Debug: Moderate (tools, metrics shown)
```

### Verbose Mode (Engineer/Admin)
```
Response Format: { success, question, answer, sources, traceability, retrieval_quality, rl_recommendation, ... }
Validation: None (raw data)
Output: Complete BI data with all metadata
Debug: Full (all details, traceability, learning stats)
```

## Testing Recommendations

1. **Ingestion Testing**
   ```bash
   # Test PDF ingestion
   agent.invoke("ingest_from_path", path="./test_docs", file_type="pdf")
   
   # Test text ingestion
   agent.invoke("ingest_from_path", path="./test_docs", file_type="text")
   
   # Test mixed ingestion
   agent.invoke("ingest_from_path", path="./test_docs", file_type="auto")
   ```

2. **Guardrails Testing**
   ```bash
   # Test concise mode validation
   agent.ask_question(question="test", response_mode="concise")
   
   # Test internal mode validation
   agent.ask_question(question="test", response_mode="internal")
   
   # Test verbose mode (no guardrails)
   agent.ask_question(question="test", response_mode="verbose")
   ```

3. **Configuration Testing**
   - Verify data_sources.json loads correctly
   - Test recursive directory scanning
   - Verify document type filtering

## Dependencies Added

- `pdfplumber` (optional) - PDF extraction with tables
- `PyPDF2` (optional) - Fallback PDF extraction
- `python-docx` (optional) - Word document extraction
- `guardrails-ai` - Response validation

All are optional with HAS_* flags to gracefully handle missing libraries.

## Benefits

✅ **Unified Ingestion**: Single interface for PDF, Text, Word documents
✅ **Configuration-Driven**: All settings in data_sources.json
✅ **Guardrails Integration**: Response mode specific validation
✅ **Recursive Discovery**: Auto-find documents in folder trees
✅ **Auto Doc_ID Generation**: File path + timestamp based IDs
✅ **Verbosity Control**: Debug output per response mode
✅ **Graceful Degradation**: Works without optional libraries
✅ **No Breaking Changes**: Existing code continues to work

## Next Steps (Optional)

1. Implement Guardrails caching for performance
2. Add custom validators for domain-specific rules
3. Implement response regeneration if validation fails
4. Add Guardrails metrics to database logging
5. Create UI for visualization of validation decisions
