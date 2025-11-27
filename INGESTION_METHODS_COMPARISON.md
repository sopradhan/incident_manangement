# Ingestion Methods Comparison: Document vs Table vs PDF

## Quick Answer

**Q: For PDF do we have any tool?**

**A:** ❌ No built-in PDF tool in `ingestion_tools.py`

**BUT:** ✅ New tool created: `pdf_ingestion_tool.py` that extracts PDFs and uses existing agent

---

## Three Ingestion Methods Explained

### Method 1: DOCUMENT INGESTION

```
Your Code:
agent.invoke("ingest_document", text="manual content here", doc_id="manual_v1")

What Happens:
  text (string)
    ↓
  ingest_document() method
    ↓
  ingestion_graph processes:
    1. extract_metadata_tool → LLM analyzes text
    2. chunk_document_tool → splits into 512-char chunks
    3. save_to_vectordb_tool → embeds and stores
  ↓
  ChromaDB stores chunks

Tool Used: None (direct string input)
Config: None required
Best For: Handbooks, policies, any raw text
```

**Example:**
```python
agent.invoke("ingest_document", 
            text="Incident Response Procedures: Step 1...",
            doc_id="incident_manual_v2")
```

---

### Method 2: TABLE INGESTION

```
Your Code:
agent.invoke("ingest_sqlite_table", table_name="knowledge_base")

What Happens:
  table_name (string)
    ↓
  invoke() method:
    ├─ Loads data_sources.json
    ├─ Finds config for "knowledge_base"
    ├─ Extracts text_columns: ["cause", "description", ...]
    └─ Extracts metadata_columns: ["id", "resource_type", ...]
  ↓
  ingest_sqlite_table_tool processes:
    1. Connects to SQLite DB
    2. Fetches all rows from table
    3. Converts each row to Markdown text
    4. Chunks each row's text
    5. Embeds and stores with metadata_columns attached
  ↓
  ChromaDB stores chunks

Tool Used: ingest_sqlite_table_tool
Config: data_sources.json (required)
Best For: Structured data, database records, logs
```

**Example:**
```python
agent.invoke("ingest_sqlite_table",
            table_name="knowledge_base")
            # Config for this table comes from data_sources.json
```

**data_sources.json:**
```json
{
  "sqlite": {
    "ingestion_modes": {
      "table_based": {
        "tables_to_ingest": [
          {
            "name": "knowledge_base",
            "text_columns": ["cause", "description", "impact"],
            "metadata_columns": ["id", "resource_type", "environment"]
          }
        ]
      }
    }
  }
}
```

---

### Method 3: PDF INGESTION (NEW)

```
Your Code:
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent
ingest_pdf_to_agent("docs/playbook.pdf", agent, doc_id="playbook_v1")

What Happens:
  PDF file (binary)
    ↓
  ingest_pdf_to_agent() function:
    1. Calls extract_pdf_text()
       ├─ Auto-detects library (pdfplumber or PyPDF2)
       ├─ Reads all pages
       ├─ Extracts text from each page
       └─ Returns plain text
    ↓
  pdf_ingestion_tool processes:
    "--- Page 1 ---\n**Title:** Playbook\n..."
    ↓
  agent.invoke("ingest_document", text=extracted_text, ...)
    ↓
  Calls same ingestion_graph as Method 1:
    1. extract_metadata_tool
    2. chunk_document_tool
    3. save_to_vectordb_tool
  ↓
  ChromaDB stores chunks

Tool Used: pdf_ingestion_tool + ingestion_graph
Config: Optional (extraction method)
Best For: PDFs, books, reports, multi-page documents
```

**Example:**
```python
from incident_iq.rag.tools.pdf_ingestion_tool import ingest_pdf_to_agent

result = ingest_pdf_to_agent("docs/incident_playbook.pdf", agent)
# Automatically extracts text and ingests to VectorDB
```

---

## Side-by-Side Comparison

```
┌─────────────────┬──────────────────┬──────────────────┬──────────────────┐
│                 │    DOCUMENT      │     TABLE        │       PDF        │
├─────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Input Type      │ String (text)    │ Table name (str) │ File path (str)  │
│ Tool Used       │ None             │ ingest_sqlite... │ pdf_ingestion... │
│ Config File     │ None             │ data_sources.json│ Optional         │
│ Pre-processing  │ None             │ SQL fetch        │ PDF extraction   │
│                 │                  │ Row → Markdown   │ PDF → Text       │
│ Metadata Source │ LLM analyzes     │ Config columns   │ LLM analyzes     │
│ Time to Ingest  │ Fast             │ Medium           │ Medium           │
│ Cost (tokens)   │ Low              │ Medium           │ Low-Medium       │
│ Scaling         │ 1 document       │ All table rows   │ Multiple PDFs    │
│ Best For        │ Handbooks        │ Structured data  │ Publications     │
│                 │ Policies         │ Database records │ Manuals          │
│                 │ Raw text         │ Logs             │ Reports          │
├─────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Invoke Code     │agent.invoke(     │agent.invoke(     │ingest_pdf_...()  │
│                 │  "ingest_        │  "ingest_        │or agent.invoke(  │
│                 │   document",     │   sqlite_table", │  "ingest_        │
│                 │  text="...",     │  table_name="kb")│   document",     │
│                 │  doc_id="doc_1") │                  │  text=extracted) │
└─────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

---

## Ingestion Workflow Comparison

### DOCUMENT
```
Your text
  ↓
LangGraphRAGAgent.invoke()
  ↓
ingest_document()
  ↓
ingestion_graph
  ├─ extract_metadata_tool
  ├─ chunk_document_tool
  ├─ save_to_vectordb_tool
  └─ update_metadata_tracking_tool
  ↓
ChromaDB + SQLite
```

### TABLE
```
Your table name
  ↓
LangGraphRAGAgent.invoke()
  ├─ Load data_sources.json
  ├─ Extract text_columns & metadata_columns
  └─ Call ingest_sqlite_table_tool
  ↓
ingest_sqlite_table_tool
  ├─ Fetch rows from SQLite
  ├─ Convert to Markdown text
  └─ Chunk and embed each row
  ↓
ChromaDB + SQLite
```

### PDF
```
Your PDF file
  ↓
pdf_ingestion_tool.extract_pdf_text()
  ├─ Auto-detect pdfplumber/PyPDF2
  ├─ Extract text from pages
  ├─ Extract tables (if available)
  └─ Return plain text
  ↓
LangGraphRAGAgent.invoke()
  ↓
ingest_document()
  ↓
ingestion_graph (same as DOCUMENT)
  ├─ extract_metadata_tool
  ├─ chunk_document_tool
  ├─ save_to_vectordb_tool
  └─ update_metadata_tracking_tool
  ↓
ChromaDB + SQLite
```

---

## Code Examples Side-by-Side

### Example 1: Single Item Ingestion

**Document:**
```python
agent.invoke("ingest_document",
            text="Procedures: Step 1...",
            doc_id="doc_001")
```

**Table:**
```python
agent.invoke("ingest_sqlite_table",
            table_name="knowledge_base")
```

**PDF:**
```python
ingest_pdf_to_agent("docs/manual.pdf", agent, doc_id="pdf_001")
```

### Example 2: Batch Processing

**Document:**
```python
docs = ["text1", "text2", "text3"]
for i, text in enumerate(docs):
    agent.invoke("ingest_document",
                text=text,
                doc_id=f"doc_{i}")
```

**Table:**
```python
for table in ["kb", "logs", "runbooks"]:
    agent.invoke("ingest_sqlite_table",
                table_name=table)
```

**PDF:**
```python
from pathlib import Path
for pdf in Path("docs").glob("*.pdf"):
    ingest_pdf_to_agent(pdf, agent)
```

### Example 3: Query After Ingestion

**All Methods:**
```python
# Same query method works for all ingestion types
result = agent.invoke("ask_question",
                     question="What are incident procedures?",
                     response_mode="concise")
print(result["answer"])
```

---

## Data in ChromaDB (Unified Format)

**Regardless of ingestion method, all chunks stored the same way:**

```python
{
    "chunk_id": "doc_001_chunk_0",
    "text": "Incident procedures step 1...",
    "embedding": [0.123, -0.456, ..., 0.789],  # 1536-dim
    "metadata": {
        "doc_id": "doc_001",
        "source_type": "document",  # or "table" or "pdf"
        "chunk_index": 0,
        "title": "Incident Procedures",
        "keywords": ["incident", "procedures", ...],
        # For tables only:
        "source_table": "knowledge_base",
        "source_record_index": 5,
        # For PDFs only:
        "page": 1,
        "pdf_path": "docs/manual.pdf"
    }
}
```

**Result:** One unified VectorDB, queryable the same way for all content types

---

## Installation Summary

| Method | Installation |
|--------|--------------|
| Document | None needed (text → string) |
| Table | None needed (uses SQLite) |
| PDF | `pip install pdfplumber PyPDF2` |

---

## When to Use Each Method

### Use DOCUMENT when:
- You have raw text (copy-paste, API response, etc.)
- You have Markdown files
- You have TXT files
- You want full control over text content

### Use TABLE when:
- You have data in SQLite database
- You want to ingest rows as documents
- You want automatic metadata extraction from columns
- You want to keep data synchronized with DB

### Use PDF when:
- You have PDF files (manuals, reports, books)
- You want automatic text extraction
- You want page tracking
- You want table extraction from PDFs

---

## The Ingestion Agent (One Agent, Multiple Methods)

**LangGraphRAGAgent** is the master orchestrator that:

1. Routes to appropriate method (document/table/PDF)
2. Pre-processes input (SQL fetch or PDF extraction)
3. Runs same ingestion workflow for all types
4. Stores in unified ChromaDB format
5. Enables unified querying

```python
agent = LangGraphRAGAgent()  # One agent

# Method 1
agent.invoke("ingest_document", ...)

# Method 2
agent.invoke("ingest_sqlite_table", ...)

# Method 3 (via helper)
ingest_pdf_to_agent(..., agent)

# All queryable same way
agent.invoke("ask_question", ...)
```

---

## Key Takeaway

```
╔═════════════════════════════════════════════════════════════╗
║ PDF Ingestion: NO built-in tool, BUT NEW tool exists!      ║
║                                                             ║
║ pdf_ingestion_tool.py:                                      ║
║   ├─ Extracts text from PDF                                ║
║   └─ Feeds to existing ingest_document() pipeline          ║
║                                                             ║
║ All three methods (Document, Table, PDF) use the same:     ║
║   ├─ LangGraphRAGAgent                                      ║
║   ├─ ingestion_graph workflow                              ║
║   ├─ ChromaDB storage                                       ║
║   └─ ask_question() for querying                           ║
║                                                             ║
║ Result: Unified RAG system supporting multiple sources     ║
╚═════════════════════════════════════════════════════════════╝
```
