# PDF Ingestion Quick Reference

## Status

✅ **NEW PDF Ingestion Tool Created:** `src/incident_iq/rag/tools/pdf_ingestion_tool.py`

## Installation

```bash
pip install pdfplumber PyPDF2
```

---

## Quick Examples

### Example 1: Extract PDF Text Only
```python
from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text

result = extract_pdf_text("docs/incident_playbook.pdf")

if result["success"]:
    print(f"Pages: {result['metadata']['pages']}")
    print(f"Method used: {result['method']}")
    print(f"Text preview:\n{result['text'][:500]}")
```

### Example 2: Full PDF → VectorDB Pipeline
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()

result = ingest_pdf_to_agent(
    pdf_path="docs/runbook.pdf",
    agent=agent,
    doc_id="runbook_v2.1"
)

print(f"Success: {result['success']}")
print(f"Chunks saved: {result['chunks_saved']}")
```

### Example 3: Batch Process Multiple PDFs
```python
from pathlib import Path
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()

for pdf in Path("docs").glob("*.pdf"):
    result = ingest_pdf_to_agent(pdf, agent)
    status = "✓" if result["success"] else "✗"
    print(f"{status} {pdf.name}: {result.get('chunks_saved', 'ERROR')}")
```

### Example 4: Query After PDF Ingestion
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()

# Ingest PDF
agent_result = ingest_pdf_to_agent(
    "docs/incident_response_manual.pdf",
    agent,
    doc_id="manual_v2024"
)

# Query
answer = agent.invoke("ask_question",
                     question="What's the incident response procedure?",
                     response_mode="concise")

print(answer["answer"])
# Shows answer pulled from PDF chunks
```

---

## Available Functions

### `extract_pdf_text(pdf_path, method="auto", include_tables=True)`

Extracts text from PDF file.

**Parameters:**
- `pdf_path` (str): Path to PDF file
- `method` (str): "auto", "pdfplumber", or "PyPDF2"
  - "auto" = Try pdfplumber first, fallback to PyPDF2
- `include_tables` (bool): Extract tables as markdown (pdfplumber only)

**Returns:**
```python
{
    "success": True/False,
    "text": "extracted text content",
    "metadata": {
        "pages": 42,
        "tables_found": 3  # pdfplumber only
    },
    "pdf_path": "docs/file.pdf",
    "method": "pdfplumber" or "PyPDF2"
}
```

### `extract_pdf_text_pdfplumber(pdf_path, include_tables=True)`

Extract using pdfplumber specifically (better for complex layouts, extracts tables).

### `extract_pdf_text_pypdf(pdf_path)`

Extract using PyPDF2 specifically (simpler, no table extraction).

### `ingest_pdf_to_agent(pdf_path, agent, doc_id=None, method="auto", include_tables=True)`

Complete pipeline: Extract PDF → Ingest to VectorDB → Return result.

**Parameters:**
- `pdf_path` (str): Path to PDF file
- `agent`: LangGraphRAGAgent instance
- `doc_id` (str): Optional ID for batch (auto-generated if not provided)
- `method` (str): PDF extraction method
- `include_tables` (bool): Extract tables

**Returns:**
```python
{
    "success": True,
    "doc_id": "pdf_filename_20241127_120000",
    "chunks_saved": 45,
    "pdf_extraction_method": "pdfplumber",
    "pdf_pages": 12,
    "pdf_tables_found": 3,
    "original_pdf_path": "docs/file.pdf"
}
```

---

## How It Works

### Architecture

```
PDF File
    ↓
pdf_ingestion_tool.extract_pdf_text()
    ├─ Detect best library (pdfplumber/PyPDF2)
    ├─ Extract text from all pages
    ├─ Extract tables if available
    └─ Return markdown-formatted text
    ↓
agent.invoke("ingest_document", text=..., doc_id="pdf_...")
    ↓
LangGraphRAGAgent.ingest_document()
    ├─ ingestion_graph executes:
    │   ├─ extract_metadata_tool (LLM analyzes)
    │   ├─ chunk_document_tool (split 512 chars)
    │   ├─ save_to_vectordb_tool (embed + store)
    │   └─ update_metadata_tracking_tool (log)
    └─ Return result with chunk count
    ↓
ChromaDB stores chunks + embeddings + metadata
    ↓
Ready for queries!
```

### Processing Steps

1. **Extract** - Read PDF pages, get text + tables
2. **Mark** - Add page markers (--- Page X ---)
3. **Chunk** - Split into ~512 char overlapping chunks
4. **Embed** - Generate 1536-dim vectors for each chunk
5. **Store** - Save to ChromaDB with metadata
6. **Track** - Log in SQLite metadata tables

---

## Library Comparison

| Feature | pdfplumber | PyPDF2 | Winner |
|---------|-----------|--------|--------|
| Text extraction | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | pdfplumber |
| Table extraction | ⭐⭐⭐⭐⭐ | ❌ | pdfplumber |
| Speed | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | PyPDF2 |
| Accuracy | ⭐⭐⭐⭐ | ⭐⭐⭐ | pdfplumber |
| Layout preservation | ⭐⭐⭐⭐ | ⭐⭐ | pdfplumber |
| Installation | Requires install | Requires install | - |
| File size | Medium | Small | PyPDF2 |

**Recommendation:** Use pdfplumber for RAG (better accuracy + table support)

---

## Common Patterns

### Pattern: Ingest PDF and Query Immediately
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()

# 1. Ingest
ingest_result = ingest_pdf_to_agent("docs/playbook.pdf", agent, "playbook_prod")
print(f"Ingested {ingest_result['chunks_saved']} chunks")

# 2. Query
answer = agent.invoke("ask_question", 
                     question="What are incident escalation procedures?",
                     doc_id="playbook_prod")
print(answer["answer"])
```

### Pattern: Process Directory of PDFs
```python
from pathlib import Path
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()
pdf_dir = Path("knowledgebase/pdfs")
results = {}

for pdf_file in sorted(pdf_dir.glob("*.pdf")):
    print(f"Processing {pdf_file.name}...")
    result = ingest_pdf_to_agent(pdf_file, agent)
    results[pdf_file.name] = result

# Summary
success = sum(1 for r in results.values() if r["success"])
print(f"\n✓ Success: {success}/{len(results)}")
```

### Pattern: Custom doc_id with Versioning
```python
from datetime import datetime
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()

# Create versioned doc_id
version = "v2.1"
timestamp = datetime.now().strftime("%Y%m%d")
doc_id = f"incident_manual_{version}_{timestamp}"

result = ingest_pdf_to_agent(
    "docs/incident_manual.pdf",
    agent,
    doc_id=doc_id
)
```

---

## Limitations

### Current (✓ Supported)
- ✅ Text extraction from standard PDFs
- ✅ Table extraction (pdfplumber)
- ✅ Multi-page PDFs
- ✅ Batch processing
- ✅ Auto-detection of best library

### Not Yet Implemented (❌)
- ❌ Scanned PDFs (OCR required)
- ❌ PDF forms
- ❌ Image extraction
- ❌ Handwritten text
- ❌ Protected/encrypted PDFs

### Workarounds for Unsupported Types

**Scanned PDFs:** Use online OCR tool first (e.g., ilovepdf.com), convert to text-based PDF

**Protected PDFs:** Unlock using Adobe or similar tool first

---

## Troubleshooting

### "pdfplumber not installed"
```bash
pip install pdfplumber
```

### "PyPDF2 not installed"
```bash
pip install PyPDF2
```

### "PDF file not found"
```python
# Check path
from pathlib import Path
pdf_path = Path("docs/file.pdf")
print(f"Exists: {pdf_path.exists()}")
print(f"Absolute: {pdf_path.absolute()}")

# Use absolute path
result = extract_pdf_text(str(pdf_path.absolute()))
```

### "No text extracted"
- Try with `method="pdfplumber"` instead of auto
- Check if PDF is scanned (requires OCR)
- Try opening PDF in Adobe Reader to verify it's readable

### "Out of memory on large PDF"
- Process PDFs in batches using page ranges
- Use smaller chunk_size
- Process fewer PDFs at once

---

## Integration with Agent Workflow

```python
# Example: Complete workflow

from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

# 1. Initialize agent
agent = LangGraphRAGAgent()

# 2. Ingest PDF
print("[1] Ingesting PDF...")
ingest = ingest_pdf_to_agent("docs/manual.pdf", agent, "manual_v1")
print(f"    ✓ {ingest['chunks_saved']} chunks saved")

# 3. Ask question (concise - user friendly)
print("\n[2] Querying (concise mode)...")
result = agent.invoke("ask_question",
    question="How do I escalate incidents?",
    response_mode="concise"
)
print(f"    Answer: {result['answer']}")

# 4. Ask question (verbose - full metadata)
print("\n[3] Querying (verbose mode)...")
result = agent.invoke("ask_question",
    question="How do I escalate incidents?",
    response_mode="verbose"
)
print(f"    Quality: {result['retrieval_quality']}")
print(f"    Sources: {result['sources_count']}")
```

---

## Next Steps

1. **Install PDF libraries:** `pip install pdfplumber PyPDF2`
2. **Test extraction:** `extract_pdf_text("path/to/pdf")`
3. **Ingest to agent:** `ingest_pdf_to_agent("path/to/pdf", agent)`
4. **Query results:** `agent.invoke("ask_question", ...)`
5. **Scale to batch:** Loop through multiple PDFs
