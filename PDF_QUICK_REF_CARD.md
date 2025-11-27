# PDF Ingestion: Quick Reference Card

## Installation (One-time)
```bash
pip install pdfplumber PyPDF2
```

---

## Use Cases & Solutions

### I want to ingest a PDF
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()
result = ingest_pdf_to_agent("docs/manual.pdf", agent)
print(f"✓ {result['chunks_saved']} chunks ingested")
```

### I want to extract PDF text (no ingestion)
```python
from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text

result = extract_pdf_text("docs/manual.pdf")
if result["success"]:
    print(result["text"])
else:
    print(f"Error: {result['error']}")
```

### I want to process multiple PDFs
```python
from pathlib import Path
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()
for pdf in Path("docs").glob("*.pdf"):
    result = ingest_pdf_to_agent(pdf, agent)
    print(f"{pdf.name}: {result.get('chunks_saved', 'ERROR')} chunks")
```

### I want to query the ingested PDF
```python
# After ingesting PDF:
result = agent.invoke("ask_question",
                     question="What's the procedure?",
                     response_mode="concise")
print(result["answer"])
```

### I want to extract with tables
```python
from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text

result = extract_pdf_text("docs/report.pdf", 
                         method="pdfplumber",  # Better for tables
                         include_tables=True)
print(f"Tables found: {result['metadata']['tables_found']}")
```

---

## Functions Quick Reference

| Function | Purpose | Returns |
|----------|---------|---------|
| `extract_pdf_text(path)` | Extract text from PDF | Dict with "text" + metadata |
| `extract_pdf_text_pdfplumber(path)` | Extract with pdfplumber | Dict with text + tables |
| `extract_pdf_text_pypdf(path)` | Extract with PyPDF2 | Dict with text |
| `ingest_pdf_to_agent(path, agent)` | Complete pipeline | Dict with ingestion result |

---

## Response Modes

After ingesting PDFs, query with three modes:

### Concise (User-friendly)
```python
result = agent.invoke("ask_question",
                     question="What's the procedure?",
                     response_mode="concise")
# Returns: {"answer": "...", "session_id": "..."}
```

### Internal (System integration)
```python
result = agent.invoke("ask_question",
                     question="What's the procedure?",
                     response_mode="internal")
# Returns: {"answer": "...", "quality_score": 0.85, "sources_count": 3}
```

### Verbose (Full metadata)
```python
result = agent.invoke("ask_question",
                     question="What's the procedure?",
                     response_mode="verbose")
# Returns: Full details + RL info + optimization data
```

---

## Common Tasks

### Task: Batch ingest all PDFs in a folder
```python
from pathlib import Path
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()

for pdf_file in Path("knowledgebase").glob("*.pdf"):
    print(f"Processing {pdf_file.name}...")
    result = ingest_pdf_to_agent(pdf_file, agent)
    
    if result["success"]:
        print(f"  ✓ {result['chunks_saved']} chunks")
    else:
        print(f"  ✗ {result['error']}")
```

### Task: Extract PDF with custom doc_id
```python
from datetime import datetime
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

doc_id = f"incident_manual_v2_{datetime.now().strftime('%Y%m%d')}"
result = ingest_pdf_to_agent("docs/manual.pdf", agent, doc_id=doc_id)
```

### Task: Extract PDF and save extracted text
```python
from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text

result = extract_pdf_text("docs/report.pdf")
if result["success"]:
    with open("report_extracted.txt", "w") as f:
        f.write(result["text"])
    print(f"Extracted to file: {result['metadata']['pages']} pages")
```

### Task: Compare extraction methods
```python
from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text

# Method 1: Auto-detect
auto = extract_pdf_text("docs/complex.pdf", method="auto")

# Method 2: pdfplumber
pdm = extract_pdf_text("docs/complex.pdf", method="pdfplumber")

# Method 3: PyPDF2
pdf2 = extract_pdf_text("docs/complex.pdf", method="PyPDF2")

print(f"Auto: {len(auto['text'])} chars")
print(f"pdfplumber: {len(pdm['text'])} chars")
print(f"PyPDF2: {len(pdf2['text'])} chars")
```

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
from pathlib import Path
pdf_path = Path("docs/file.pdf")
print(f"Exists: {pdf_path.exists()}")  # Check if file exists
print(f"Path: {pdf_path.absolute()}")  # See absolute path

# Use absolute path
result = extract_pdf_text(str(pdf_path.absolute()))
```

### "No text extracted from PDF"
```python
# Try pdfplumber specifically (more robust)
result = extract_pdf_text("docs/file.pdf", method="pdfplumber")

# Check if it's a scanned PDF
if not result["success"] or len(result["text"]) < 100:
    print("Might be a scanned PDF (requires OCR)")
```

### "ImportError: No module named pdf_ingestion_tool"
```python
# Make sure you're in the right directory
# And using correct import path
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

# Or check file exists
from pathlib import Path
pdf_tool = Path("src/incident_iq/rag/tools/pdf_ingestion_tool.py")
print(f"Tool exists: {pdf_tool.exists()}")
```

---

## Response Structure

### extract_pdf_text() response
```python
{
    "success": True,
    "text": "--- Page 1 ---\n**Title:** ...",
    "metadata": {
        "pages": 12,
        "tables_found": 3  # Only if pdfplumber
    },
    "pdf_path": "docs/file.pdf",
    "method": "pdfplumber"  # or "PyPDF2"
}
```

### ingest_pdf_to_agent() response
```python
{
    "success": True,
    "doc_id": "pdf_manual_20241127_120000",
    "chunks_saved": 45,
    "pdf_extraction_method": "pdfplumber",
    "pdf_pages": 12,
    "pdf_tables_found": 3,
    "original_pdf_path": "docs/file.pdf",
    "errors": []
}
```

### ask_question() response (concise)
```python
{
    "success": True,
    "question": "What's the procedure?",
    "answer": "The procedure is...",
    "session_id": "uuid-...",
    "errors": []
}
```

---

## Data Flow Summary

```
PDF File
  ↓
extract_pdf_text()      ← Extracts text
  ↓
ingest_pdf_to_agent()   ← Calls agent.invoke()
  ↓
LangGraphRAGAgent
  ├─ extract_metadata_tool
  ├─ chunk_document_tool
  ├─ save_to_vectordb_tool
  └─ update_metadata_tracking_tool
  ↓
ChromaDB + SQLite
  ↓
agent.invoke("ask_question", ...)
  ↓
User gets answer with sources
```

---

## All Ingestion Methods

| Method | Code | Installation |
|--------|------|--------------|
| Document | `agent.invoke("ingest_document", text="...")` | None |
| Table | `agent.invoke("ingest_sqlite_table", table_name="...")` | None |
| **PDF** | `ingest_pdf_to_agent("path", agent)` | `pip install pdfplumber PyPDF2` |

---

## Key Points

✅ **PDF ingestion is now available**
✅ **No code changes to agent needed**
✅ **Reuses existing ingestion pipeline**
✅ **Works with all query modes** (concise/verbose/internal)
✅ **Auto-detects best PDF library**
✅ **Supports table extraction**
✅ **Batch processing ready**
✅ **Integrated with ChromaDB + SQLite**

---

## One-Liner Examples

```python
# Install
pip install pdfplumber PyPDF2

# Extract
from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text; extract_pdf_text("file.pdf")

# Ingest
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent; ingest_pdf_to_agent("file.pdf", agent)

# Query
agent.invoke("ask_question", question="What's the procedure?")
```

---

## Documentation Files

- `INGESTION_GUIDE.md` - Full ingestion documentation
- `PDF_INGESTION_QUICK_REF.md` - Detailed reference
- `PDF_INGESTION_SUMMARY.md` - Complete guide
- `INGESTION_METHODS_COMPARISON.md` - Comparison of all methods
- `PDF_INGESTION_CREATED.md` - What was created
- **This file** - Quick reference card
