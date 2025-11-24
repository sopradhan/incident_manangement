# SQLite Table Ingestion - Generic Framework for ANY Table

## Summary

The ingestion system now supports **any SQLite table** configured in `data_sources.json`. No code changes needed - just configuration.

## Quick Start - Adding a New Table

### Step 1: Edit `data_sources.json`

Add your table to the `tables_to_ingest` array:

```json
{
  "name": "your_table_name",
  "enabled": true,
  "description": "What this table contains",
  "text_columns": ["column_a", "column_b", "column_c"],
  "metadata_columns": ["id", "category", "timestamp"],
  "chunk_strategy": "per_record",
  "where_clause": null
}
```

### Step 2: Run Ingestion

```python
from src.incident_iq.rag.agents.ingestion_agent import IngestionAgent

ingestion_agent = IngestionAgent(services, config)

# Option A: Ingest all configured tables
result = ingestion_agent.ingest_all_configured_tables()

# Option B: Ingest specific table
result = ingestion_agent.ingest_sqlite_table({
    "name": "your_table_name",
    "text_columns": ["column_a", "column_b"],
    "metadata_columns": ["id", "category"],
    "chunk_strategy": "per_record"
})

print(result)
```

### Step 3: Query Results

```python
# After ingestion, query across all tables
retrieval_result = retrieval_agent.retrieve(
    query="Your question here",
    top_k=5
)

# Results include table name in metadata
for source in retrieval_result['sources']:
    print(f"Table: {source['metadata']['table']}")
    print(f"Text: {source['text']}")
```

## Configuration Fields

| Field | Type | Required | Example | Notes |
|-------|------|----------|---------|-------|
| `name` | string | Yes | `"knowledge_base"` | SQLite table name |
| `enabled` | bool | No | `true` | Enable/disable ingestion |
| `description` | string | No | `"Incident KB"` | For documentation |
| `text_columns` | array | Yes | `["title", "content"]` | Columns to search |
| `metadata_columns` | array | No | `["id", "category"]` | Columns as metadata |
| `chunk_strategy` | string | No | `"per_record"` | `"per_record"` or `"sequential"` |
| `where_clause` | string | No | `"status='active'"` | SQL filter |

## Chunk Strategies

### `per_record` (Default)
- One document per database row
- Best for: Knowledge bases, FAQs, policies
- Metadata: Preserved per record

```
Row 1 → Document 1 → Chunks
Row 2 → Document 2 → Chunks
Row 3 → Document 3 → Chunks
```

### `sequential`
- Multiple rows combined into one document
- Best for: Incident timelines, related data
- Metadata: Aggregated from all rows

```
Rows 1-3 → Document 1 → Chunks
Rows 4-5 → Document 2 → Chunks
```

## Examples

### Example 1: Knowledge Base (Existing)

```json
{
  "name": "knowledge_base",
  "enabled": true,
  "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
  "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"],
  "chunk_strategy": "per_record"
}
```

### Example 2: Policies Table

```json
{
  "name": "policies",
  "enabled": true,
  "description": "Company policies",
  "text_columns": ["policy_title", "policy_content", "guidelines"],
  "metadata_columns": ["policy_id", "category", "department", "effective_date"],
  "chunk_strategy": "per_record",
  "where_clause": "status = 'active'"
}
```

### Example 3: FAQs

```json
{
  "name": "faqs",
  "enabled": true,
  "text_columns": ["question", "answer", "related_topics"],
  "metadata_columns": ["faq_id", "category", "last_updated", "view_count"],
  "chunk_strategy": "per_record"
}
```

### Example 4: Incident Timeline (Sequential)

```json
{
  "name": "incident_events",
  "enabled": true,
  "text_columns": ["event_description", "action_taken", "result"],
  "metadata_columns": ["incident_id", "event_id", "timestamp", "severity"],
  "chunk_strategy": "sequential"
}
```

## Complete Example: Multi-Table Setup

`data_sources.json`:

```json
{
  "data_sources": {
    "sqlite": {
      "enabled": true,
      "ingestion_modes": {
        "table_based": {
          "enabled": true,
          "tables_to_ingest": [
            {
              "name": "knowledge_base",
              "enabled": true,
              "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
              "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"],
              "chunk_strategy": "per_record"
            },
            {
              "name": "policies",
              "enabled": true,
              "text_columns": ["policy_title", "policy_content"],
              "metadata_columns": ["policy_id", "category", "department"],
              "chunk_strategy": "per_record",
              "where_clause": "status = 'active'"
            },
            {
              "name": "faqs",
              "enabled": true,
              "text_columns": ["question", "answer"],
              "metadata_columns": ["faq_id", "category"],
              "chunk_strategy": "per_record"
            },
            {
              "name": "incidents",
              "enabled": false,
              "text_columns": ["title", "description", "resolution"],
              "metadata_columns": ["incident_id", "severity"],
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
}
```

## Ingestion Methods

### Method 1: Ingest All Configured Tables

```python
result = ingestion_agent.ingest_all_configured_tables()
```

Returns:
```python
{
  "success": True,
  "total_tables": 3,
  "successful_tables": 3,
  "total_records_processed": 150,
  "total_chunks_created": 450,
  "table_results": [
    {"table": "knowledge_base", "success": True, "records_processed": 45, "chunks_created": 128},
    {"table": "policies", "success": True, "records_processed": 30, "chunks_created": 95},
    {"table": "faqs", "success": True, "records_processed": 75, "chunks_created": 227}
  ]
}
```

### Method 2: Ingest Single Table

```python
result = ingestion_agent.ingest_sqlite_table({
    "name": "policies",
    "text_columns": ["policy_title", "policy_content"],
    "metadata_columns": ["policy_id", "category"],
    "chunk_strategy": "per_record"
})
```

Returns:
```python
{
  "success": True,
  "table_name": "policies",
  "records_processed": 30,
  "documents_created": 30,
  "total_chunks_created": 95,
  "chunks": [...]
}
```

### Method 3: Using Ingestion Tool Directly

```python
from src.incident_iq.rag.tools.ingestion_tools import ingest_sqlite_table_tool

result_json = ingest_sqlite_table_tool(
    table_name="policies",
    text_columns=["policy_title", "policy_content"],
    metadata_columns=["policy_id", "category"],
    llm_service=llm_service,
    vectordb_service=vectordb_service,
    chunk_strategy="per_record",
    where_clause="status = 'active'"
)

result = json.loads(result_json)
```

## What Gets Stored in Vector DB

Each chunk includes:

```python
{
  "id": "policies_doc_0_chunk_0_1234567890",
  "text": "Full text of the chunk from text_columns",
  "embedding": [0.234, -0.156, 0.892, ...],  # 384-dim semantic vector
  "metadata": {
    "table": "policies",           # Which table
    "document_index": 0,           # Which record (per_record) or doc (sequential)
    "chunk_index": 0,              # Chunk number within document
    "chunk_strategy": "per_record",
    "source_records": 1,           # 1 for per_record, N for sequential
    "policy_id": 1,                # Original metadata columns
    "category": "Compliance",
    "department": "Engineering"
  }
}
```

## Filtering and WHERE Clauses

Only ingest specific records:

```json
{
  "name": "policies",
  "where_clause": "status = 'active' AND department = 'Engineering'"
}
```

```json
{
  "name": "incidents",
  "where_clause": "severity IN ('critical', 'high') AND year(date_created) = 2024"
}
```

## Cross-Table Queries

After ingesting multiple tables, queries automatically search across all:

```python
# This query searches knowledge_base, policies, faqs, and incidents
result = retrieval_agent.retrieve(
    query="What should I do if a customer data breach occurs?",
    top_k=10
)

# Results include chunks from different tables
for source in result['sources']:
    if source['metadata']['table'] == 'policies':
        print(f"Policy: {source['text']}")
    elif source['metadata']['table'] == 'knowledge_base':
        print(f"KB: {source['text']}")
```

## Performance Notes

- **Per-record strategy**: Faster ingestion, better for individual records
- **Sequential strategy**: Slower ingestion (combines records), better for context
- **WHERE clause**: Reduces records processed, speeds up ingestion
- **Metadata columns**: Don't affect chunk size, just attached to results

## Troubleshooting

### Table not found error
```
Error: Table 'my_table' does not exist in database
```
Check:
- Table name spelling in `data_sources.json`
- Table exists in SQLite database
- Using correct database path

### No records found error
```
Error: No records found in table 'my_table'
```
Check:
- Table has data
- `where_clause` isn't filtering out all records
- Data types in `where_clause` are correct

### Column not found error
```
Error: Column 'nonexistent' not in row
```
Check:
- Column names match exactly (case-sensitive)
- Columns exist in table schema
- No typos in `text_columns` or `metadata_columns`

## Full Implementation Location

- **Config loader**: `src/incident_iq/rag/agents/ingestion_agent.py::TableIngestionConfig`
- **Ingestion tool**: `src/incident_iq/rag/tools/ingestion_tools.py::ingest_sqlite_table_tool()`
- **Agent methods**: `src/incident_iq/rag/agents/ingestion_agent.py::IngestionAgent`
- **Config file**: `src/incident_iq/rag/config/data_sources.json`

---

**The system is completely generic and config-driven. Add any table to `data_sources.json` and it will be ingested into your RAG pipeline automatically!**
