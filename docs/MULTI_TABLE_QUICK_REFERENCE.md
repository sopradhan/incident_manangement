# Multi-Table SQLite Ingestion - Quick Reference

## ✅ What's New

You can now ingest **ANY SQLite table** with just configuration changes - no code modifications needed.

## 🚀 Quick Start (3 Steps)

### 1. Add table to `data_sources.json`

```json
{
  "name": "policies",
  "enabled": true,
  "text_columns": ["policy_title", "policy_content"],
  "metadata_columns": ["policy_id", "category"],
  "chunk_strategy": "per_record"
}
```

### 2. Run ingestion

```python
ingestion_agent.ingest_all_configured_tables()
```

### 3. Query results

```python
retrieval_agent.retrieve("Your question", top_k=5)
```

Results automatically include all ingested tables!

## 📋 Generic Table Schema

```json
{
  "name": "table_name",
  "enabled": true,
  "description": "Optional description",
  "text_columns": ["col1", "col2"],      // Searchable columns
  "metadata_columns": ["id", "type"],    // Non-searchable metadata
  "chunk_strategy": "per_record",        // or "sequential"
  "where_clause": "status='active'"      // Optional SQL filter
}
```

## 🔧 Real Examples

### Example 1: knowledge_base (Existing)
```json
{
  "name": "knowledge_base",
  "enabled": true,
  "text_columns": ["cause", "description", "impact", "remediation_steps", "rca"],
  "metadata_columns": ["id", "resource_type", "environment", "dollar_impact"],
  "chunk_strategy": "per_record"
}
```

### Example 2: policies
```json
{
  "name": "policies",
  "enabled": true,
  "text_columns": ["policy_title", "policy_content", "guidelines"],
  "metadata_columns": ["policy_id", "category", "department", "effective_date"],
  "chunk_strategy": "per_record",
  "where_clause": "status = 'active'"
}
```

### Example 3: faqs
```json
{
  "name": "faqs",
  "enabled": true,
  "text_columns": ["question", "answer"],
  "metadata_columns": ["faq_id", "category"],
  "chunk_strategy": "per_record"
}
```

### Example 4: incidents (Sequential)
```json
{
  "name": "incidents",
  "enabled": true,
  "text_columns": ["title", "description", "timeline"],
  "metadata_columns": ["incident_id", "severity", "assigned_to"],
  "chunk_strategy": "sequential"  // Combine multiple rows
}
```

## 💻 Code Examples

### Ingest All Tables
```python
result = ingestion_agent.ingest_all_configured_tables()
print(f"Ingested {result['total_tables']} tables")
print(f"Total chunks: {result['total_chunks_created']}")
```

### Ingest Single Table
```python
result = ingestion_agent.ingest_sqlite_table({
    "name": "policies",
    "text_columns": ["policy_title", "policy_content"],
    "metadata_columns": ["policy_id", "category"],
    "chunk_strategy": "per_record"
})
```

### Query Result Format
```python
result = retrieval_agent.retrieve("Query", top_k=5)

# Results include which table each chunk came from
for source in result['sources']:
    table = source['metadata']['table']  # "policies", "knowledge_base", etc.
    text = source['text']
    print(f"From {table}: {text}")
```

## 📊 Chunk Strategies

### `per_record` (Default)
- **One document per database row**
- Best for: Knowledge bases, policies, FAQs
- Result: 1 row = 1 document = multiple chunks

```
Row 1 → Document → Chunks 1, 2, 3
Row 2 → Document → Chunks 1, 2
Row 3 → Document → Chunks 1
```

### `sequential`
- **Multiple rows combined into one document**
- Best for: Incident timelines, related data
- Result: Multiple rows = 1 document = multiple chunks

```
Rows 1-10 → Document → Chunks 1, 2, 3
Rows 11-20 → Document → Chunks 1, 2, 3
```

## 🔍 Search Example

Query that searches across ALL ingested tables:

```python
# After ingesting knowledge_base, policies, faqs
result = retrieval_agent.retrieve(
    query="What is our password policy?",
    top_k=10
)

# Automatic results from multiple tables ranked by relevance
[
  {
    "text": "Passwords must be at least 16 characters...",
    "table": "policies",
    "similarity": 0.95
  },
  {
    "text": "How do I reset my password?",
    "table": "faqs",
    "similarity": 0.82
  },
  {
    "text": "Password reset failed due to...",
    "table": "knowledge_base",
    "similarity": 0.71
  }
]
```

## 🛠️ How It Works

```
data_sources.json
    ↓
TableIngestionConfig.load_sqlite_tables()
    ↓
ingest_all_configured_tables()
    ↓
For each table:
  - Read from database
  - Apply where_clause filter (if any)
  - Convert to documents (per_record or sequential)
  - Split semantically (512 tokens, 50 overlap)
  - Generate embeddings
  - Store in Chroma with metadata
    ↓
Vector DB ready for semantic search
    ↓
Query searches ALL tables automatically
```

## 📝 Configuration Location

- **Config file**: `src/incident_iq/rag/config/data_sources.json`
- **Config loader**: `src/incident_iq/rag/agents/ingestion_agent.py::TableIngestionConfig`
- **Ingestion tool**: `src/incident_iq/rag/tools/ingestion_tools.py::ingest_sqlite_table_tool()`
- **Agent class**: `src/incident_iq/rag/agents/ingestion_agent.py::IngestionAgent`

## ✨ Key Features

✅ **Generic** - Works with any SQLite table  
✅ **Config-driven** - No code changes needed  
✅ **Flexible** - Multiple chunk strategies  
✅ **Filterable** - Optional WHERE clauses  
✅ **Cross-table** - Queries search all tables  
✅ **Traceable** - Metadata shows source table  

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| "Table not found" | Check table name spelling in config |
| "No records" | Verify table has data, check where_clause |
| "Column not found" | Check column names match exactly |
| Missing results | Ensure table is `enabled: true` in config |

## 📚 For More Info

- `DATABASE_TABLE_INGESTION_EXPLAINED.md` - Detailed concept guide
- `SQLITE_TABLE_INGESTION_GENERIC.md` - Complete reference with all examples
- Docstrings in `ingestion_agent.py` and `ingestion_tools.py`

---

**That's it! The system is completely generic and config-driven. Just add your table to data_sources.json and run ingestion.**
