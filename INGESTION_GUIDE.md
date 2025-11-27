# Ingestion Guide: Documents vs Tables

## What is `doc_id`?

**`doc_id` is NOT a document path** - it's a **unique identifier** for a batch of ingested content. Think of it like a batch tracking number.

```
doc_id examples:
- "sqlite_knowledge_base"      ← For SQLite table ingestion
- "doc_incident_manual_2024"   ← For document ingestion
- "user_uploads_batch_001"     ← For multiple documents
- "policy_handbook_v2"         ← For handbook documents
```

### doc_id Purpose
1. **Tracking**: Groups all chunks from one ingestion into one batch
2. **Metadata**: Stored with every chunk for traceability
3. **Retrieval**: Can filter results by `doc_id` if needed
4. **Cleanup**: Easy to delete/reindex an entire batch

---

## How Ingestion Works: Document vs Table

### **DOCUMENT INGESTION** (Text/PDF files)

```
Pipeline: Text File → Extract Metadata → Chunk Text → Embed → Store in VectorDB
```

**Flow:**
1. You pass raw text (from file, PDF, API, etc.)
2. `extract_metadata_tool` - LLM analyzes text → extracts title, summary, keywords, doc_type
3. `chunk_document_tool` - Splits text into chunks (500 chars, 50 overlap default)
4. `save_to_vectordb_tool` - Generates embeddings for each chunk, stores in ChromaDB

**Example - Document Ingestion:**
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Read a document
with open("incident_response_manual.txt", "r") as f:
    text = f.read()

# Ingest it
result = agent.invoke("ingest_document", 
                     text=text,
                     doc_id="incident_manual_2024")

print(result)
# Output:
# {
#     "success": True,
#     "doc_id": "incident_manual_2024",
#     "chunks_count": 42,
#     "chunks_saved": 42,
#     "metadata": {"title": "Incident Response Manual", ...},
#     "errors": []
# }
```

---

### **TABLE INGESTION** (SQLite database rows)

```
Pipeline: SQLite Table → Fetch Rows → Convert to Markdown Text → Chunk → Embed → Store
```

**Flow:**
1. Connects to SQLite database
2. Reads all rows from specified table
3. Converts each row to **structured Markdown text** (combines text_columns)
4. Chunks each document
5. Embeds and stores with **metadata_columns** attached

**Example - Table Ingestion:**
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Ingest SQLite table (config-driven)
result = agent.invoke("ingest_sqlite_table",
                     table_name="knowledge_base",
                     doc_id="sqlite_kb_prod_20241127")

print(result)
# Output:
# {
#     "success": True,
#     "table_name": "knowledge_base",
#     "doc_id": "sqlite_kb_prod_20241127",
#     "records_processed": 150,
#     "chunks_created": 450,
#     "chunks_saved": 450,
#     "statistics": {...},
#     "errors": []
# }
```

---

## Configuration: data_sources.json

**Location:** `src/incident_iq/rag/config/data_sources.json`

```json
{
  "data_sources": {
    "sqlite": {
      "ingestion_modes": {
        "table_based": {
          "tables_to_ingest": [
            {
              "name": "knowledge_base",
              "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
              "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"]
            },
            {
              "name": "incident_logs",
              "text_columns": ["event_description", "system_logs"],
              "metadata_columns": ["timestamp", "severity", "service_name"]
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

### Configuration Fields:

| Field | Purpose | Example |
|-------|---------|---------|
| `text_columns` | Columns combined for embeddings | `["cause", "description", "impact"]` |
| `metadata_columns` | Columns attached to each chunk | `["id", "resource_type", "environment"]` |
| `chunk_size` | Max chars per chunk | `512` |
| `overlap` | Chars shared between chunks | `50` |

---

## PDF Ingestion (Currently No Built-in Tool)

**Current Status:** ❌ **NO dedicated PDF tool exists** in `ingestion_tools.py`

However, you can still ingest PDFs by extracting text first, then using the document ingestion pipeline.

### **How to Ingest PDFs:**

#### **Option 1: Pre-extract PDF to Text (Recommended)**

```python
# Step 1: Extract PDF text using PyPDF or pdfplumber
# (These are NOT in requirements.txt, you need to install them)

# Option A: Using PyPDF (simple, light)
from PyPDF2 import PdfReader

pdf_path = "docs/incident_playbook.pdf"
reader = PdfReader(pdf_path)

text = ""
for page_num, page in enumerate(reader.pages):
    text += f"\n--- Page {page_num + 1} ---\n"
    text += page.extract_text()

# Step 2: Ingest extracted text as document
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()
result = agent.invoke("ingest_document",
                     text=text,
                     doc_id="pdf_incident_playbook_v2")

print(f"✓ Ingested {result['chunks_saved']} chunks from PDF")
```

#### **Option B: Using pdfplumber (Better for complex layouts)**

```python
import pdfplumber
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

pdf_path = "docs/technical_runbook.pdf"

with pdfplumber.open(pdf_path) as pdf:
    text = ""
    for page_num, page in enumerate(pdf.pages):
        text += f"\n--- Page {page_num + 1} ---\n"
        text += page.extract_text()
        
        # Optional: Extract tables on page
        tables = page.extract_tables()
        if tables:
            text += "\n**Tables on this page:**\n"
            for table in tables:
                # Convert table to markdown
                for row in table:
                    text += " | ".join(str(cell) for cell in row) + "\n"

agent = LangGraphRAGAgent()
result = agent.invoke("ingest_document",
                     text=text,
                     doc_id="pdf_runbook_technical")
```

### **PDF Ingestion Architecture:**

```
PDF File (incident_playbook.pdf)
    ↓
[EXTERNAL] PyPDF/pdfplumber library
    ↓ Extract text + tables
Plain Text + Markdown
    ↓
agent.invoke("ingest_document", text=extracted_text, doc_id="pdf_...")
    ↓
LangGraphRAGAgent.ingest_document()
    ↓
ingestion_graph workflow:
  ├─ extract_metadata_tool (LLM analyzes text)
  ├─ chunk_document_tool (splits into 512-char chunks)
  ├─ save_to_vectordb_tool (embeds, stores in ChromaDB)
  └─ update_metadata_tracking_tool (logs in SQLite)
    ↓
Chunks stored in Vector DB with metadata
```

### **PDF Ingestion Architecture:**

```
PDF File (incident_playbook.pdf)
    ↓
[EXTERNAL] PyPDF/pdfplumber library
    ↓ Extract text + tables
Plain Text + Markdown
    ↓
agent.invoke("ingest_document", text=extracted_text, doc_id="pdf_...")
    ↓
LangGraphRAGAgent.ingest_document()
    ↓
ingestion_graph workflow:
  ├─ extract_metadata_tool (LLM analyzes text)
  ├─ chunk_document_tool (splits into 512-char chunks)
  ├─ save_to_vectordb_tool (embeds, stores in ChromaDB)
  └─ update_metadata_tracking_tool (logs in SQLite)
    ↓
Chunks stored in Vector DB with metadata
```

### **PDF Processing Best Practices:**

| Library | Pros | Cons | Use Case |
|---------|------|------|----------|
| **PyPDF** | Simple, lightweight, no extra deps | Less accurate on complex layouts | Clean PDFs, basic extraction |
| **pdfplumber** | Excellent table extraction, accurate | Requires install | PDFs with tables, complex layouts |
| **pdf2image + pytesseract** | Handles scanned PDFs (OCR) | Slower, needs system deps | Scanned/image PDFs |

### **Using the PDF Ingestion Tool (Recommended)**

A dedicated PDF ingestion tool is available at `src/incident_iq/rag/tools/pdf_ingestion_tool.py`.

#### **Installation (One-time):**

```bash
pip install pdfplumber PyPDF2
```

#### **Usage Example 1: Simple PDF Extraction**

```python
from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text

# Extract PDF text (auto-detects best library)
result = extract_pdf_text("docs/incident_playbook.pdf")

if result["success"]:
    print(f"Extracted {result['metadata']['pages']} pages")
    print(result["text"][:500])  # First 500 chars
else:
    print(f"Error: {result['error']}")
```

#### **Usage Example 2: Complete PDF Ingestion Pipeline**

```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()

# One-line PDF ingestion (extract + chunk + embed + store)
result = ingest_pdf_to_agent(
    pdf_path="docs/technical_runbook.pdf",
    agent=agent,
    doc_id="pdf_runbook_tech_v2",
    include_tables=True
)

print(f"✓ Success: {result['success']}")
print(f"✓ Chunks saved: {result['chunks_saved']}")
print(f"✓ PDF method: {result['pdf_extraction_method']}")
print(f"✓ Pages: {result['pdf_pages']}")
print(f"✓ Tables found: {result['pdf_tables_found']}")
```

#### **Usage Example 3: Batch PDF Ingestion**

```python
from pathlib import Path
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

agent = LangGraphRAGAgent()
pdf_directory = Path("docs/pdfs")

# Ingest all PDFs in directory
for pdf_file in pdf_directory.glob("*.pdf"):
    print(f"\n[Processing] {pdf_file.name}")
    
    result = ingest_pdf_to_agent(
        pdf_path=str(pdf_file),
        agent=agent,
        # doc_id auto-generated: pdf_filename_YYYYMMDD_HHMMSS
    )
    
    if result["success"]:
        print(f"  ✓ Ingested {result['chunks_saved']} chunks")
    else:
        print(f"  ✗ Failed: {result['error']}")
```

#### **Usage Example 4: Specify Extraction Method**

```python
from incident_iq.rag.tools.pdf_ingestion_tool import extract_pdf_text

# Use pdfplumber specifically (best for tables)
result = extract_pdf_text(
    "docs/complex_report.pdf",
    method="pdfplumber",
    include_tables=True
)

# Use PyPDF2 specifically (simpler, faster)
result = extract_pdf_text(
    "docs/simple_doc.pdf",
    method="PyPDF2"
)
```

### **What Happens During PDF Ingestion:**

```
1. Extract PDF Text
   ├─ Read all pages
   ├─ Extract text from each page
   ├─ Extract tables (if pdfplumber)
   └─ Combine into single markdown document

2. Chunk Document
   ├─ Split into ~512 character chunks
   ├─ 50 char overlap between chunks
   └─ Assign chunk IDs (pdf_runbook_0, pdf_runbook_1, ...)

3. Generate Embeddings
   ├─ For each chunk, generate 1536-dim embedding
   └─ Store embedding vector

4. Store in VectorDB (ChromaDB)
   ├─ Store chunk text
   ├─ Store embedding
   ├─ Store metadata (doc_id, page_num, pdf_path)
   └─ Make searchable

5. Query
   ├─ User asks: "What are runbook procedures?"
   ├─ Embed question (same 1536-dim)
   ├─ Find similar chunks via vector similarity
   ├─ Return top results with page numbers
   └─ Show which PDF chunks were used
```

### **Handling Different PDF Types:**

**Clean, Text-based PDFs** (recommended for RAG):
```python
result = extract_pdf_text("docs/clean_policy.pdf", method="auto")
```

**PDFs with Complex Layouts & Tables** (use pdfplumber):
```python
result = extract_pdf_text("docs/complex_report.pdf", method="pdfplumber", include_tables=True)
```

**Scanned PDFs (OCR required)** - NOT YET SUPPORTED:
```
Would need: pdf2image + pytesseract (Tesseract OCR)
Currently not implemented in pdf_ingestion_tool.py
Can be added if needed
```

---

## How The Agent + Tool Work Together

### **Architecture:**

```
┌──────────────────────────────────────┐
│ LangGraphRAGAgent.invoke()           │ User calls one method
└────────────┬─────────────────────────┘
             │
             ├─ operation="ingest_document"
             │  │
             │  └─→ ingest_document()
             │      │
             │      └─→ ingestion_graph (LangGraph workflow)
             │          ├─→ extract_metadata_tool
             │          ├─→ chunk_document_tool
             │          ├─→ save_to_vectordb_tool
             │          └─→ update_metadata_tracking_tool
             │
             └─ operation="ingest_sqlite_table"
                │
                └─→ invoke() method
                    │
                    ├─ Loads data_sources.json
                    ├─ Extracts table config
                    ├─ Calls ingest_sqlite_table_tool
                    │  ├─ Fetch rows from SQLite
                    │  ├─ Convert to Markdown text
                    │  ├─ Generate embeddings (llm_service)
                    │  └─ Store in ChromaDB (vectordb_service)
                    │
                    └─ Returns result
```

### **Code Flow for Table Ingestion:**

```python
# Step 1: User calls invoke()
agent.invoke("ingest_sqlite_table", table_name="knowledge_base")

# Step 2: invoke() method (in langgraph_rag_agent.py)
# - Loads data_sources.json
# - Finds config for "knowledge_base" table
# - Extracts: text_columns, metadata_columns, chunk_size, overlap
config_path = Path(__file__).parent.parent.parent / "config" / "data_sources.json"
config = json.load(open(config_path))
table_config = next((t for t in tables_config if t.get("name") == "knowledge_base"), {})
text_columns = table_config.get("text_columns", [])  # ["cause", "description", "impact", ...]
metadata_columns = table_config.get("metadata_columns", [])  # ["id", "resource_type", ...]

# Step 3: Calls ingest_sqlite_table_tool with config values
result_json = ingest_sqlite_table_tool.invoke({
    "table_name": "knowledge_base",
    "doc_id": "sqlite_knowledge_base",
    "text_columns": text_columns,
    "metadata_columns": metadata_columns,
    "llm_service": self.llm_service,
    "vectordb_service": self.vectordb_service,
    "chunk_size": 512,
    "chunk_overlap": 50
})

# Step 4: Tool processes table (ingest_sqlite_table_tool)
# a) Connect to SQLite, fetch rows
conn = sqlite3.connect(db_path)
rows = cursor.execute(f"SELECT * FROM {table_name}").fetchall()

# b) Convert each row to Markdown-style text
for row in rows:
    # Example row: {id: 123, cause: "Network timeout", description: "..."}
    text = """--- Table Record: knowledge_base (Index: 0) ---
**Cause:** Network timeout
**Description:** Service unable to reach database...
**Impact:** Transactions failed
**Remediation Steps:** Restart service
**Rca:** Connection pool exhausted"""
    
    # c) Chunk it
    chunks = splitter.split_text(text)  # e.g., 3 chunks
    
    # d) Embed each chunk
    for chunk in chunks:
        embedding = llm_service.generate_embedding(chunk)  # 1536-dim vector
        
        # e) Save to VectorDB with metadata
        vectordb_service.collection.add(
            ids=["sqlite_knowledge_base_0_0", "sqlite_knowledge_base_0_1", ...],
            documents=[chunk1, chunk2, ...],
            embeddings=[emb1, emb2, ...],
            metadatas=[
                {"id": 123, "resource_type": "database", "doc_id": "sqlite_knowledge_base"},
                {"id": 123, "resource_type": "database", "doc_id": "sqlite_knowledge_base"},
                ...
            ]
        )

# Step 5: Return results
return {
    "success": True,
    "records_processed": 150,
    "chunks_created": 450,
    "chunks_saved": 450
}
```

---

## Full Usage Examples

### **Example 1: Ingest Document (From File)**
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Read document
with open("docs/incident_playbook.md", "r") as f:
    content = f.read()

# Ingest
result = agent.invoke("ingest_document",
                     text=content,
                     doc_id="playbook_v2.1")

print(f"✓ Ingested {result['chunks_saved']} chunks")
```

### **Example 2: Ingest SQLite Table (Configuration-Driven)**
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Configuration is in data_sources.json automatically
result = agent.invoke("ingest_sqlite_table",
                     table_name="knowledge_base")

print(f"✓ Ingested {result['records_processed']} records → {result['chunks_saved']} chunks")
```

### **Example 3: Query After Ingestion**
```python
# After ingesting, ask questions
result = agent.invoke("ask_question",
                     question="What causes network timeouts?",
                     response_mode="concise")

print(result["answer"])
# Output: "Network timeouts are caused by..."
```

### **Example 4: Verbose Mode Shows Chunk Sources**
```python
result = agent.invoke("ask_question",
                     question="What is the RCA for database issues?",
                     response_mode="verbose")

# Shows which chunks were retrieved
for source in result["sources"]:
    print(f"- Chunk: {source['metadata']['chunk_id']}")
    print(f"  From table: {source['metadata']['source_table']}")
    print(f"  From doc_id: {source['metadata']['doc_id']}")
```

---

## Chunk Structure in Vector DB

### **What gets stored:**

```
Chunk ID:      "sqlite_knowledge_base_0_0"
                └─ doc_id_record_idx_chunk_idx

Text:          "**Cause:** Network timeout
                 **Description:** Service unable to reach..."

Embedding:     [0.123, -0.456, 0.789, ...]  (1536 dimensions)

Metadata:      {
                  "id": 123,                          ← From metadata_columns
                  "resource_type": "database",       ← From metadata_columns
                  "environment": "production",       ← From metadata_columns
                  "source_table": "knowledge_base",  ← Automatic
                  "doc_id": "sqlite_knowledge_base",  ← Your doc_id
                  "source_record_index": 0,          ← Row number in table
                  "chunk_index": 0,                  ← Chunk position
                  "doc_type": "table_record"         ← Automatic
                }
```

When you query "What causes issues?", the system:
1. Embeds your question (1536 dims)
2. Searches VectorDB for similar chunks
3. Returns chunks with metadata intact
4. You can see which table row it came from (`source_record_index`)

---

## Key Differences Summary

| Aspect | Document | Table |
|--------|----------|-------|
| **Input** | Raw text (file, string) | SQLite table name |
| **Configuration** | None required | data_sources.json required |
| **Metadata** | Extracted by LLM | From specified columns |
| **Scaling** | 1-N documents | All rows in table |
| **doc_id** | Your choice | "sqlite_tablename" |
| **Use case** | Handbooks, policies, PDFs | Structured data, logs |

---

## Common Patterns

### **Pattern 1: Batch Ingest Multiple Tables**
```python
agent = LangGraphRAGAgent()

for table in ["knowledge_base", "incident_logs", "runbooks"]:
    result = agent.invoke("ingest_sqlite_table", table_name=table)
    print(f"✓ {table}: {result['chunks_saved']} chunks")
```

### **Pattern 2: Selective Table Ingestion with WHERE Clause**
```python
# Ingest only specific rows (requires modification)
result = agent.invoke("ingest_sqlite_table",
                     table_name="knowledge_base",
                     where_clause="environment = 'production'")
```

### **Pattern 3: Custom doc_id for Versioning**
```python
from datetime import datetime

doc_id = f"knowledge_base_v1_{datetime.now().strftime('%Y%m%d')}"

result = agent.invoke("ingest_sqlite_table",
                     table_name="knowledge_base",
                     doc_id=doc_id)
```
