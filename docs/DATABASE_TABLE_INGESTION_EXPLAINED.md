# Database Table Ingestion Explained

## What is Database Table Ingestion?

**Ingestion** is the process of converting raw data into a searchable, queryable format that your RAG system can use. For database tables specifically, it means:

1. **Reading structured data** from ANY SQLite table (knowledge_base, policies, incidents, etc.)
2. **Converting database records into documents** (text documents)
3. **Extracting and preserving metadata** (important fields)
4. **Chunking documents semantically** (breaking into meaningful pieces)
5. **Creating embeddings** (semantic vectors for similarity search)
6. **Storing in vector database** (Chroma) with metadata for retrieval

## Why Ingest Database Tables?

### Traditional Database Query Problems
```sql
-- Traditional SQL search: only keyword matching
SELECT * FROM knowledge_base WHERE description LIKE '%memory%'
-- Returns only exact keyword matches, misses similar concepts
```

### RAG Ingestion Solution
```
Database Table (structured data)
    ↓
Convert to documents (semantic text)
    ↓
Create embeddings (understand meaning)
    ↓
Vector DB (find similar concepts)
    ↓
Result: "What causes memory issues?" → finds "Memory leak" + "Process using too much RAM"
```

## Your Configuration - Generic for ANY Table

In `data_sources.json`, you have a **generic framework** that works with any SQLite table:

```json
{
  "sqlite": {
    "enabled": true,
    "description": "Ingest data from any SQLite3 database table",
    "ingestion_modes": {
      "table_based": {
        "enabled": true,
        "tables_to_ingest": [
          {
            "name": "knowledge_base",
            "enabled": true,
            "description": "Main incident knowledge base",
            "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
            "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"],
            "chunk_strategy": "per_record"
          },
          {
            "name": "policies",
            "enabled": false,
            "description": "Company policies and procedures",
            "text_columns": ["policy_title", "policy_content", "guidelines"],
            "metadata_columns": ["policy_id", "category", "department", "effective_date"],
            "chunk_strategy": "per_record",
            "where_clause": "status = 'active'"
          },
          {
            "name": "incidents",
            "enabled": false,
            "description": "Historical incident reports",
            "text_columns": ["title", "description", "resolution"],
            "metadata_columns": ["incident_id", "severity", "assigned_to", "created_date"],
            "chunk_strategy": "sequential"
          }
        ]
      }
    },
    "chunking": {
      "enabled": true,
      "strategy": "semantic",
      "chunk_size": 512,
      "overlap": 50
    }
  }
}
```

### Key Features:

✅ **Add any table** - Just add to `tables_to_ingest` array  
✅ **Configure text columns** - Which columns contain searchable content  
✅ **Configure metadata columns** - Which columns are metadata only  
✅ **Filter records** - Optional `where_clause` for conditional ingestion  
✅ **Two chunk strategies** - `per_record` or `sequential`  
✅ **Config-driven** - No code changes needed to add new tables  

## How It Works - Step by Step

### Step 1: Define Table Configuration

Example: Adding a "policies" table to ingestion:

```json
{
  "name": "policies",
  "enabled": true,
  "description": "Company policies and procedures",
  "text_columns": ["policy_title", "policy_content", "guidelines"],
  "metadata_columns": ["policy_id", "category", "department", "effective_date"],
  "chunk_strategy": "per_record",
  "where_clause": "status = 'active'"
}
```

### Step 2: Per-Record Chunking

The `"chunk_strategy": "per_record"` means each database record becomes one document:

**policies table:**

```
policy_id  policy_title           policy_content               category         department
1          Data Privacy Policy    "Handle sensitive data..."   Compliance       Engineering
2          Code Review Standards  "All code must be..."        Development      Engineering
3          Vacation Policy        "Employees get 20 days..."   HR               HR
```

**Record 1 → Document 1**
```
policy_title: Data Privacy Policy
policy_content: Handle sensitive data according to GDPR...
guidelines: [content]

[Metadata attached:]
- policy_id: 1
- category: "Compliance"
- department: "Engineering"
- effective_date: "2024-01-01"
```

**Record 2 → Document 2**
```
policy_title: Code Review Standards
policy_content: All code must be peer-reviewed...
guidelines: [content]

[Metadata attached:]
- policy_id: 2
- category: "Development"
- department: "Engineering"
- effective_date: "2023-06-01"
```

### Step 3: Sequential Chunking Alternative

Example: Combining multiple records into one document

```json
{
  "name": "incidents",
  "chunk_strategy": "sequential"
}
```

**Multiple records combined:**
```
--- Record 1 ---
title: API Outage
description: Service was down for 2 hours...

--- Record 2 ---
title: Database Timeout
description: Query performance degraded...

--- Record 3 ---
title: Memory Leak
description: Service memory usage increased...
```

Then semantically chunked into meaningful 512-token pieces.

### Step 4: Semantic Chunking

Each document is split using semantic chunking (512 tokens, 50 overlap):

**Document 1 becomes:**
```
Chunk 1.1 (512 tokens):
"policy_title: Data Privacy Policy. policy_content: Handle sensitive data..."
[overlap: 50 tokens]

Chunk 1.2 (512 tokens):
"[50 token overlap]...GDPR requirements and compliance standards..."
```

### Step 5: Embedding Creation

Each chunk gets converted to a semantic embedding (vector):

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

chunk = "policy_title: Data Privacy Policy. policy_content: Handle sensitive data..."
embedding = model.encode(chunk)  # [0.234, -0.156, 0.892, ...] (384 dimensions)
```

### Step 6: Vector Database Storage

All chunks stored in Chroma with their embeddings and metadata:

```python
{
  "id": "policies_doc_0_chunk_0_1234567890",
  "text": "policy_title: Data Privacy Policy. policy_content: Handle sensitive data...",
  "embedding": [0.234, -0.156, 0.892, ...],
  "metadata": {
    "table": "policies",
    "document_index": 0,
    "chunk_index": 0,
    "chunk_strategy": "per_record",
    "policy_id": 1,
    "category": "Compliance",
    "department": "Engineering",
    "effective_date": "2024-01-01"
  }
}
```

## The Complete Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  SQLite Database (ANY table configured)                 │
│  - knowledge_base                                       │
│  - policies                                             │
│  - incidents                                            │
│  - [ANY OTHER TABLE]                                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ Read from data_sources.json config
                 │ Apply optional WHERE clause filter
                 ↓
┌─────────────────────────────────────────────────────────┐
│  ingest_sqlite_table_tool() [Generic]                   │
│  - Validates table exists                               │
│  - Reads all records (or filtered)                       │
│  - Converts to documents                                │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ Apply chunk_strategy
                 │ - per_record: 1 doc per row
                 │ - sequential: combine all rows
                 ↓
┌─────────────────────────────────────────────────────────┐
│  RecursiveCharacterTextSplitter                         │
│  Semantic chunking: 512 tokens, 50 overlap              │
│  Creates: Chunk 1, Chunk 2, Chunk 3, etc.              │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ Generate embeddings for each chunk
                 │ Attach metadata (from metadata_columns)
                 ↓
┌─────────────────────────────────────────────────────────┐
│  Chroma Vector Database                                 │
│  - All chunks with embeddings                           │
│  - Original database metadata attached                  │
│  - Ready for semantic similarity search                 │
└─────────────────────────────────────────────────────────┘
```

## Usage Examples

### 1. Ingest Knowledge Base (already configured)

```python
from src.incident_iq.rag.agents.ingestion_agent import IngestionAgent

ingestion_agent = IngestionAgent(services, config)

# Ingest single table
result = ingestion_agent.ingest_sqlite_table({
    "name": "knowledge_base",
    "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
    "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"],
    "chunk_strategy": "per_record"
})

print(result)
# Output:
# {
#   "success": True,
#   "table_name": "knowledge_base",
#   "records_processed": 45,
#   "documents_created": 45,
#   "total_chunks_created": 128,
#   "chunks": [...]
# }
```

### 2. Ingest All Configured Tables

```python
# Ingest all tables that are enabled in data_sources.json
result = ingestion_agent.ingest_all_configured_tables()

print(result)
# Output:
# {
#   "success": True,
#   "total_tables": 3,
#   "successful_tables": 3,
#   "total_records_processed": 150,
#   "total_chunks_created": 450,
#   "table_results": [
#     {"table": "knowledge_base", "success": True, "records_processed": 45, "chunks_created": 128},
#     {"table": "policies", "success": True, "records_processed": 30, "chunks_created": 95},
#     {"table": "incidents", "success": True, "records_processed": 75, "chunks_created": 227}
#   ]
# }
```

### 3. Add New Table to Configuration

Edit `data_sources.json`:

```json
{
  "name": "faqs",
  "enabled": true,
  "description": "Frequently Asked Questions",
  "text_columns": ["question", "answer", "related_topics"],
  "metadata_columns": ["faq_id", "category", "last_updated", "view_count"],
  "chunk_strategy": "per_record"
}
```

Then ingest:

```python
result = ingestion_agent.ingest_all_configured_tables()
# Automatically includes new "faqs" table!
```

### 4. Query Ingested Tables

After ingestion, query across all tables:

```python
retrieval_result = retrieval_agent.retrieve(
    query="What is our data privacy policy?",
    top_k=5
)

# Results include:
# 1. Chunks from "policies" table (policy_content)
# 2. Chunks from "knowledge_base" table (if related)
# 3. Chunks from "incidents" table (if related)
# All ranked by semantic similarity

print(retrieval_result['sources'])
# [
#   {
#     "chunk_id": "policies_doc_0_chunk_0_...",
#     "text": "Data Privacy Policy...",
#     "metadata": {"table": "policies", "category": "Compliance", ...}
#   },
#   ...
# ]
```

## Example Query After Ingestion

### User Asks:
```
"What is our data privacy policy and who handles it?"
```

### RAG System Processing:

1. **Convert query to embedding:**
   ```python
   query_embedding = model.encode("What is our data privacy policy?")
   # [0.156, -0.234, 0.721, ...]
   ```

2. **Semantic search across ALL ingested tables:**
   ```python
   results = chroma_collection.query(
       query_embeddings=[query_embedding],
       n_results=5
   )
   # Searches knowledge_base, policies, incidents, and any other ingested tables
   ```

3. **Retrieve matching chunks (from multiple tables):**
   ```
   ✓ "policy_title: Data Privacy Policy. policy_content: All personal data must be..."
     table: "policies"
     similarity: 0.94
     metadata: {category: "Compliance", department: "Engineering", effective_date: "2024-01-01"}
   
   ✓ "Data breach incident: Customer data was exposed due to..."
     table: "incidents"
     similarity: 0.71
     metadata: {severity: "high", assigned_to: "john@company.com"}
   ```

4. **Return with all metadata preserved:**
   ```json
   {
     "answer": "Our Data Privacy Policy requires all personal data to be encrypted and handled per GDPR standards. Handled by the Engineering department, effective since 2024-01-01.",
     "sources": [
       {
         "table": "policies",
         "chunk_id": "policies_doc_0_chunk_0_...",
         "category": "Compliance",
         "department": "Engineering"
       }
     ],
     "confidence": 0.94
   }
   ```

## Text Columns vs Metadata Columns

### Text Columns (`text_columns`)
Used to create the searchable document content:
```
- Combined into one searchable document
- Searched during semantic similarity matching
- Examples: cause, description, policy_title, question, answer
```

### Metadata Columns (`metadata_columns`)
Attached to chunks but NOT searched directly:
```
- Used for filtering results
- Used for RBAC (which user can see this)
- Used for context in responses
- Used for analytics
- Examples: id, category, department, resource_type, environment
```

## Implementation

## Advanced: Filtering Records with WHERE Clause

Only ingest active policies:

```json
{
  "name": "policies",
  "text_columns": ["policy_title", "policy_content"],
  "metadata_columns": ["policy_id", "status"],
  "where_clause": "status = 'active'"
}
```

Only ingest high-severity incidents:

```json
{
  "name": "incidents",
  "text_columns": ["title", "description"],
  "metadata_columns": ["incident_id", "severity"],
  "where_clause": "severity IN ('critical', 'high')"
}
```

## Chunking Strategies

### per_record (One document per row)

✅ Preserves database record integrity  
✅ Metadata stays associated with full context  
✅ Easy to trace back to original record  
✅ Prevents mixing different records  
✅ **Best for**: Knowledge bases, FAQs, policies  

```
Row 1 → Document 1 → Chunks 1.1, 1.2, 1.3
Row 2 → Document 2 → Chunks 2.1, 2.2
Row 3 → Document 3 → Chunks 3.1, 3.2, 3.3
```

### sequential (Multiple rows per document)

✅ Combines related records for context  
✅ Better for time-series or related data  
✅ **Best for**: Incident timelines, historical data  

```
Row 1, Row 2, Row 3 → Document 1 → Chunks 1.1, 1.2, 1.3
Row 4, Row 5 → Document 2 → Chunks 2.1, 2.2
```

## Configuration Template for New Tables

When adding a new table to ingest, use this template:

```json
{
  "name": "table_name",
  "enabled": true,
  "description": "What this table contains",
  "text_columns": [
    "column_for_searching_1",
    "column_for_searching_2"
  ],
  "metadata_columns": [
    "id_or_primary_key",
    "category_or_type",
    "timestamp_or_date"
  ],
  "chunk_strategy": "per_record",
  "where_clause": null
}
```

## Benefits of RAG Ingestion Over Raw SQL

| Operation | SQL Only | RAG Ingestion |
|-----------|----------|---------------|
| **Exact match** | "memory" finds exactly "memory" | ✓ ✓ ✓ |
| **Synonyms** | "memory issue" ≠ "RAM problem" | ✗ | ✓ ✓ ✓ |
| **Semantic similarity** | "What causes slowness?" won't find "timeout" | ✗ | ✓ ✓ ✓ |
| **Context** | Returns raw rows | ✗ | ✓ Context + metadata |
| **Ranking** | No relevance ranking | ✗ | ✓ By similarity |
| **LLM answers** | Raw data to LLM | ✗ | ✓ Ranked sources |
| **Cross-table** | Need joins | ✓ Limited | ✓ Automatic |

## Implementation Architecture

### IngestionAgent Methods

```python
# 1. Load configuration from data_sources.json
TableIngestionConfig.load_sqlite_tables()
TableIngestionConfig.get_chunking_config()

# 2. Ingest single table
ingest_sqlite_table(table_config: Dict) -> Dict

# 3. Ingest all configured tables
ingest_all_configured_tables() -> Dict

# 4. Ingestion tool (used by all methods)
ingest_sqlite_table_tool(
    table_name,
    text_columns,
    metadata_columns,
    chunk_strategy,
    where_clause
) -> str (JSON)
```

### Ingestion Tool Features

```python
ingest_sqlite_table_tool(
    table_name="any_table",          # Any SQLite table
    text_columns=[...],              # Columns to search
    metadata_columns=[...],          # Columns for metadata
    db_path=None,                    # Uses config if None
    llm_service=...,                 # For embeddings
    vectordb_service=...,            # For storage (Chroma)
    chunk_size=512,                  # Token size
    chunk_overlap=50,                # Overlap tokens
    chunk_strategy="per_record",     # or "sequential"
    where_clause=None                # Optional SQL filter
)
```

## Next Steps

1. **Edit data_sources.json** - Add any new table to `tables_to_ingest`
2. **Define columns** - Specify text_columns and metadata_columns
3. **Choose strategy** - Use `per_record` or `sequential`
4. **Add filters** - Optional `where_clause` for conditional ingestion
5. **Run ingestion** - Call `ingest_all_configured_tables()`
6. **Query results** - Use `RetrievalAgent` for semantic search

---

**Summary**: Database table ingestion converts any SQLite table into a semantic search engine. The system is completely generic and config-driven - no code changes needed to add new tables!
