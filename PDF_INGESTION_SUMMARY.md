# PDF Ingestion: Complete Summary

## ❌ Current Status: NO Built-in PDF Tool in ingestion_tools.py

The existing `ingestion_tools.py` contains:
- ✅ `extract_metadata_tool` - LLM extracts metadata from text
- ✅ `chunk_document_tool` - Splits text into chunks
- ✅ `save_to_vectordb_tool` - Embeds and stores chunks
- ✅ `ingest_sqlite_table_tool` - SQLite table ingestion
- ❌ `ingest_pdf_tool` - NOT PRESENT

## ✅ Solution: NEW PDF Ingestion Tool Created

**File:** `src/incident_iq/rag/tools/pdf_ingestion_tool.py`

This is a standalone tool that:
1. Extracts text from PDFs (using pdfplumber or PyPDF2)
2. Integrates with LangGraphRAGAgent
3. Uses existing ingestion workflow to chunk and embed

---

## How PDF Ingestion Works

### Full Pipeline

```
PDF File (e.g., incident_playbook.pdf)
    ↓
pdf_ingestion_tool.extract_pdf_text()
    ├─ Auto-detect library (pdfplumber/PyPDF2)
    ├─ Extract text from all pages
    ├─ Extract tables (pdfplumber only)
    ├─ Format as markdown with page markers
    └─ Return: {"text": "...", "metadata": {...}}
    ↓
agent.invoke("ingest_document", text=extracted_text, doc_id="pdf_...")
    ↓
LangGraphRAGAgent.ingest_document()
    ├─ Runs ingestion_graph workflow
    │   ├─ extract_metadata_tool
    │   │   └─ LLM analyzes first 2000 chars
    │   │   └─ Extracts: title, summary, keywords, topics, doc_type
    │   │
    │   ├─ chunk_document_tool
    │   │   ├─ Splits on: "\n\n##", "\n\n", "\n", ". ", " "
    │   │   ├─ Max 512 chars per chunk
    │   │   ├─ 50 char overlap between chunks
    │   │   └─ Result: [chunk_0, chunk_1, ...]
    │   │
    │   ├─ save_to_vectordb_tool
    │   │   ├─ For each chunk:
    │   │   │   ├─ Generate embedding (1536-dim vector)
    │   │   │   ├─ Create metadata dict
    │   │   │   └─ Add to ChromaDB collection
    │   │   │
    │   │   └─ Save to SQLite
    │   │       ├─ DocumentMetadataModel
    │   │       └─ ChunkEmbeddingDataModel
    │   │
    │   └─ update_metadata_tracking_tool
    │       └─ Log in DocumentTrackingModel
    │
    └─ Return result
    ↓
Chunks stored in ChromaDB with embeddings
    └─ Ready for semantic search and querying
```

### Step-by-Step Example

**Step 1: Extract PDF**
```python
from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text

result = extract_pdf_text("docs/runbook.pdf")
# Returns:
# {
#   "success": True,
#   "text": "--- Page 1 ---\n**Runbook Title:** ...\n**Procedures:** ...",
#   "metadata": {"pages": 12, "tables_found": 2},
#   "pdf_path": "docs/runbook.pdf",
#   "method": "pdfplumber"
# }
```

**Step 2: Extract Metadata (inside ingestion graph)**
```
LLM reads first 2000 chars:
"--- Page 1 ---
**Runbook Title:** Incident Response Procedures
**Procedures:** Step 1: Alert... Step 2: Triage... ..."

LLM generates:
{
  "title": "Incident Response Procedures",
  "summary": "Guide for incident response including alert, triage, remediation",
  "keywords": ["incident", "response", "triage", "escalation", "runbook"],
  "topics": ["incident-response", "procedures", "operations"],
  "doc_type": "technical_doc"
}
```

**Step 3: Chunk Document**
```
Input text (12 pages = ~10,000 chars) becomes:
- chunk_0: "--- Page 1 ---\n**Runbook Title:**..." (512 chars, 0-512)
- chunk_1: "...Step 2: Triage..." (512 chars, 462-974) ← 50 char overlap
- chunk_2: "...Step 3: Remediation..." (512 chars, 924-1436)
- ... total ~20 chunks
```

**Step 4: Embed & Store**
```
For each chunk:
1. Generate embedding:
   embedding = llm_service.generate_embedding("--- Page 1 ---\n**Runbook Title:**...")
   → [0.123, -0.456, 0.789, ..., 0.042]  (1536 dimensions)

2. Store in ChromaDB:
   vectordb_service.collection.add(
       ids=["pdf_runbook_chunk_0", "pdf_runbook_chunk_1", ...],
       documents=[chunk_text_0, chunk_text_1, ...],
       embeddings=[emb_0, emb_1, ...],
       metadatas=[
           {"doc_id": "pdf_runbook", "page": 1, "title": "..."},
           {"doc_id": "pdf_runbook", "page": 1, "title": "..."},
           ...
       ]
   )
```

**Step 5: Query**
```python
result = agent.invoke("ask_question", 
                     question="What's the incident triage procedure?")

# System finds similar chunks:
# - chunk_2: "--- Page 2 ---\n**Step 2: Triage...[high similarity]
# - chunk_3: "...Triage checklist...[medium similarity]"
# - chunk_1: "...Alert procedures...[lower similarity]"

# Returns answer from most relevant chunks
```

---

## Complete Usage Examples

### Example 1: One-Line PDF Ingestion
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()

result = ingest_pdf_to_agent("docs/incident_playbook.pdf", agent)
print(f"✓ Ingested {result['chunks_saved']} chunks from PDF")
print(f"✓ Used {result['pdf_extraction_method']}")
print(f"✓ PDF pages: {result['pdf_pages']}")
print(f"✓ Tables found: {result['pdf_tables_found']}")
```

### Example 2: Extract PDF Only (No Ingestion)
```python
from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text

result = extract_pdf_text("docs/manual.pdf", method="pdfplumber", include_tables=True)

if result["success"]:
    text = result["text"]
    pages = result["metadata"]["pages"]
    tables = result["metadata"]["tables_found"]
    print(f"Extracted {pages} pages with {tables} tables")
else:
    print(f"Error: {result['error']}")
```

### Example 3: Batch Process Multiple PDFs
```python
from pathlib import Path
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()

for pdf_file in Path("docs").glob("**/*.pdf"):
    print(f"\nProcessing {pdf_file.name}...")
    result = ingest_pdf_to_agent(pdf_file, agent)
    
    if result["success"]:
        print(f"  ✓ Saved {result['chunks_saved']} chunks")
    else:
        print(f"  ✗ Error: {result['error']}")
```

### Example 4: PDF → Query Workflow
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()

# 1. Ingest PDF
print("[1] Ingesting PDF...")
ingest_result = ingest_pdf_to_agent(
    "docs/incident_response_manual.pdf",
    agent,
    doc_id="manual_prod"
)
print(f"    ✓ {ingest_result['chunks_saved']} chunks")

# 2. Query with concise response (user-friendly)
print("\n[2] Query (Concise)...")
answer = agent.invoke("ask_question",
                     question="What's the incident escalation procedure?",
                     response_mode="concise")
print(f"    {answer['answer']}")

# 3. Query with verbose response (full metadata)
print("\n[3] Query (Verbose)...")
verbose = agent.invoke("ask_question",
                      question="What's the incident escalation procedure?",
                      response_mode="verbose")
print(f"    Quality Score: {verbose['retrieval_quality']:.2f}")
print(f"    Source Chunks: {verbose['sources_count']}")
for source in verbose['sources'][:2]:
    print(f"      - {source['metadata']['doc_id']}")
```

---

## Agent + Tool Architecture

### **LangGraphRAGAgent Methods**

```python
agent = LangGraphRAGAgent()

# Method 1: Ingest document (already supported)
agent.invoke("ingest_document", text="...", doc_id="doc_001")

# Method 2: Ingest SQLite table (already supported)
agent.invoke("ingest_sqlite_table", table_name="knowledge_base")

# Method 3: Ask question (already supported)
agent.invoke("ask_question", question="...", response_mode="concise")

# Method 4: Optimize system (already supported)
agent.invoke("optimize", performance_history=[...])
```

### **PDF Tool (New)**

```python
from incident_iq.rag.tools.pdf_ingestion_tool import (
    extract_pdf_text,
    extract_pdf_text_pdfplumber,
    extract_pdf_text_pypdf,
    ingest_pdf_to_agent
)

# Function 1: Extract PDF text
result = extract_pdf_text("path/to/pdf.pdf")

# Function 2: Use pdfplumber specifically
result = extract_pdf_text_pdfplumber("path/to/pdf.pdf", include_tables=True)

# Function 3: Use PyPDF2 specifically
result = extract_pdf_text_pypdf("path/to/pdf.pdf")

# Function 4: Complete pipeline (recommended)
result = ingest_pdf_to_agent("path/to/pdf.pdf", agent)
```

### **Data Flow**

```
User
  ↓
ingest_pdf_to_agent(pdf_path, agent)
  ├─ extract_pdf_text()
  │   ├─ Check if pdfplumber available → use it
  │   │   OR fall back to PyPDF2
  │   └─ Return: {"text": "...", "metadata": {...}}
  │
  └─ agent.invoke("ingest_document", text=..., doc_id="pdf_...")
      └─ LangGraphRAGAgent.ingest_document()
          └─ self.ingestion_graph.invoke()
              ├─ extract_metadata_tool
              ├─ chunk_document_tool
              ├─ save_to_vectordb_tool
              └─ update_metadata_tracking_tool
                  └─ ChromaDB + SQLite stores chunks
                      ↓
                      Ready for queries!
```

---

## Comparison: Document vs Table vs PDF Ingestion

| Aspect | Document | Table | PDF |
|--------|----------|-------|-----|
| **Input** | Raw text string | SQLite table name | PDF file path |
| **Pre-processing** | None | SQL fetch | PDF extraction |
| **Configuration** | None | data_sources.json | Optional |
| **Extraction Tool** | N/A | ingest_sqlite_table_tool | pdf_ingestion_tool |
| **Metadata Source** | LLM analysis | Table columns | LLM analysis |
| **Use Case** | Handbooks, policies | Structured data | Publications, manuals |
| **Scaling** | One document | All table rows | Multiple PDFs |
| **Cost** | Low | Medium | Low-Medium |

---

## Installation

```bash
# Install PDF libraries
pip install pdfplumber PyPDF2

# Verify installation
python -c "import pdfplumber; import PyPDF2; print('✓ PDF libraries ready')"
```

---

## Key Files

| File | Purpose |
|------|---------|
| `src/incident_iq/rag/tools/pdf_ingestion_tool.py` | PDF extraction & ingestion |
| `src/incident_iq/rag/tools/ingestion_tools.py` | Core ingestion pipeline (not PDF-specific) |
| `src/incident_iq/rag/agents/langgraph_agent/langgraph_rag_agent.py` | Master orchestrator |
| `src/incident_iq/rag/config/data_sources.json` | Configuration for table ingestion |

---

## How Ingestion Agent Works (All Methods)

```python
# All ingestion flows through LangGraphRAGAgent.invoke()

agent.invoke("ingest_document", text="...", doc_id="doc_1")
agent.invoke("ingest_sqlite_table", table_name="kb")
agent.invoke("ingest_pdf_to_agent", pdf_path="file.pdf")  # Via helper function

# All eventually call:
# 1. ingestion_graph with proper state
# 2. extract_metadata_tool (LLM)
# 3. chunk_document_tool (split)
# 4. save_to_vectordb_tool (embed + store)
# 5. update_metadata_tracking_tool (log)
```

**Result:** All content types (documents, tables, PDFs) stored in same ChromaDB with same schema, queryable with same `ask_question()` method.

---

## Next Steps

1. **Install:** `pip install pdfplumber PyPDF2`
2. **Test:** `python -c "from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text"`
3. **Ingest:** `ingest_pdf_to_agent("docs/file.pdf", agent)`
4. **Query:** `agent.invoke("ask_question", question="...")`
5. **Scale:** Batch process multiple PDFs
