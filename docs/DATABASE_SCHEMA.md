# SQLite Database Schema - RAG Metadata Tables

## Entity Relationship Diagram (ERD)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    RAG SYSTEM METADATA SCHEMA                            │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐         ┌──────────────────────────┐
│   document_metadata         │         │   embedding_metadata     │
├─────────────────────────────┤         ├──────────────────────────┤
│ PK metadata_id (INTEGER)    │         │ PK embedding_id          │
│    doc_id (TEXT)◄───────────┼─────────┤    document_id (TEXT)    │
│    key (TEXT)               │         │    chunk_id (TEXT)       │
│    value (TEXT)             │         │    chunk_strategy (TEXT) │
│                             │         │    chunk_size (INTEGER)  │
│ Stored metadata:            │         │    overlap (INTEGER)     │
│ • title                     │         │    embedding_model       │
│ • author                    │         │    embedding_version     │
│ • source                    │         │    quality_score (REAL)  │
│ • created_date              │         │    last_modified (TS)    │
│ • summary                   │         │    reindex_count (INT)   │
│ • keywords                  │         │    rbac_namespace (TEXT) │
│ • categories                │         │    metadata_tags (JSON)  │
│ • doc_type                  │         │    healing_suggestions   │
│                             │         │    (TEXT)                │
└─────────────────────────────┘         └──────────────────────────┘
          △                                      △
          │                                      │
          │ Stores info about                   │ Stores info about
          │ documents ingested                  │ chunks created from
          │                                      │ documents
          │                                      │
    [INGESTION PHASE]                    [INGESTION PHASE]
    Updates for each                      Updates for each
    document ingested                     chunk created


┌──────────────────────────────┐
│      query_heatmap           │
├──────────────────────────────┤
│ PK heatmap_id (INTEGER)      │
│    query_hash (TEXT)         │
│    query_example (TEXT)      │
│    frequency (INTEGER)       │
│    avg_retrieval_accuracy    │
│    (REAL)                    │
│    avg_response_time_ms      │
│    (INTEGER)                 │
│    avg_user_feedback (REAL)  │
│    quality_category (TEXT)   │
│    last_queried (TIMESTAMP)  │
│                              │
│ Categories:                  │
│ • cold (rare)               │
│ • warm (medium)             │
│ • hot (frequent)            │
│                              │
└──────────────────────────────┘
           △
           │
           │ Updated every query
           │ Tracks performance metrics
           │ and popularity
           │
    [RETRIEVAL PHASE]
    One entry per unique query
    (or similar query pattern)


┌──────────────────────────────────┐
│    healing_operations            │
├──────────────────────────────────┤
│ PK healing_id (INTEGER)          │
│    strategy (TEXT)               │
│    target_docs (JSON)            │
│    reason (TEXT)                 │
│    actions_taken (JSON)          │
│    before_metrics (JSON)         │
│    after_metrics (JSON)          │
│    improvement_delta (REAL)      │
│    timestamp (TIMESTAMP)         │
│                                  │
│ Strategies:                      │
│ • re_chunk (adjust chunking)    │
│ • re_embed (regenerate embeds) │
│ • quality_adjustment            │
│ • context_filtering             │
│                                  │
└──────────────────────────────────┘
           △
           │ Updates when healing
           │ is triggered
           │ Tracks optimization
           │ history and results
           │
    [OPTIMIZATION PHASE]
    Created when quality < 60% or
    insufficient results or
    performance history analysis


┌──────────────────────────────┐
│   synthetic_queries          │
├──────────────────────────────┤
│ PK synthetic_id (INTEGER)    │
│    doc_id (TEXT)◄────────────┼─────── [document_metadata]
│    question (TEXT)           │
│    expected_answer (TEXT)    │
│    generated_date (TIMESTAMP)│
│    last_tested (TIMESTAMP)   │
│    test_accuracy (REAL)      │
│                              │
│ Auto-generated test questions│
│ for quality validation       │
│                              │
└──────────────────────────────┘
           △
           │ Updates during
           │ ingestion
           │ Stores synthetic Q&A
           │ pairs for testing
           │
    [INGESTION PHASE]
    Created per document
    for quality testing
```

---

## Data Flow Through Tables

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE DATA FLOW                               │
└──────────────────────────────────────────────────────────────────────────┘

PHASE 1: INGESTION
════════════════════════════════════════════════════════════════════════════

  Raw Document Input
         │
         ├─→ extract_metadata_tool
         │   └─→ INSERT INTO document_metadata
         │       (title, author, source, summary, keywords, etc.)
         │
         ├─→ chunk_document_tool  
         │   └─→ Create chunks in memory
         │
         ├─→ save_to_vectordb_tool
         │   ├─→ ChromaDB (vector storage)
         │   └─→ INSERT INTO embedding_metadata
         │       (chunk_id, quality_score, chunk_strategy, etc.)
         │
         └─→ extract_metadata_tool also creates
             └─→ INSERT INTO synthetic_queries
                 (Auto-generated test Q&A pairs)

  Status: 3-4 table inserts per document


PHASE 2: RETRIEVAL (INTELLIGENT)
════════════════════════════════════════════════════════════════════════════

  User Question
         │
         ├─→ retrieve_context_tool
         │   ├─→ Query ChromaDB
         │   └─→ Calculate retrieval_quality metric
         │
         ├─→ rerank_context_tool
         │   └─→ Sort results by relevance
         │
         ├─→ check_optimization_needed [DECISION NODE]
         │   ├─→ quality < 0.6?
         │   ├─→ results < 3?
         │   └─→ performance_history exists?
         │
         ├─→ IF YES → optimize_context:
         │   ├─→ get_context_cost_tool()
         │   │   └─→ Calculate tokens and cost
         │   │
         │   ├─→ optimize_chunk_size_tool()
         │   │   └─→ Suggest parameters
         │   │
         │   └─→ INSERT INTO healing_operations
         │       (strategy, reason, improvement_delta, etc.)
         │
         ├─→ answer_question_tool
         │   └─→ Generate final answer using LLM
         │
         ├─→ traceability_tool
         │   └─→ Create source attribution
         │
         └─→ [ALWAYS] UPDATE query_heatmap
             (frequency++, accuracy, response_time, feedback)

  Status: 1-2 table operations per query
          (1 if no healing, 2+ if healing applied)


PHASE 3: OPTIMIZATION/HEALING (CONDITIONAL)
════════════════════════════════════════════════════════════════════════════

  When Healing is Triggered:
         │
         ├─→ INSERT INTO healing_operations
         │   ├─ strategy: re_chunk, re_embed, etc.
         │   ├─ target_docs: documents affected
         │   ├─ reason: why healing was triggered
         │   ├─ improvement_delta: % improvement
         │   └─ before/after_metrics: comparison
         │
         └─→ UPDATE embedding_metadata
             ├─ quality_score: new score
             ├─ chunk_size: new size
             ├─ overlap: new overlap
             ├─ reindex_count++
             └─ healing_suggestions: tips for next time

  Status: 1-2 table updates per healing operation


SUMMARY TABLE UPDATES:
════════════════════════════════════════════════════════════════════════════

  Table                    | Ingestion | Retrieval | Optimization
  ─────────────────────────┼───────────┼───────────┼──────────────
  document_metadata        |    ✓ INS  |     -     |      -
  embedding_metadata       |    ✓ INS  |     -     |    ✓ UPD
  synthetic_queries        |    ✓ INS  |     -     |      -
  query_heatmap            |     -     |  ✓ INS/UPD|    ✓ UPD
  healing_operations       |     -     |     -     |    ✓ INS
```

---

## Table Relationships Summary

```
DOCUMENT METADATA TABLE
├─ One record per metadata item (title, author, source, etc)
├─ Multiple rows per document (doc_id)
├─ Updated: During ingestion only
└─ Query: Get all metadata for a document by doc_id

EMBEDDING METADATA TABLE  
├─ One record per chunk (chunk_id)
├─ Multiple rows per document (document_id)
├─ Updated: Ingestion (INSERT), Optimization (UPDATE quality_score)
├─ Tracks: Quality scores, chunking strategy, reindex count
└─ Query: Find low-quality chunks for healing

QUERY HEATMAP TABLE
├─ One record per unique query (query_hash)
├─ Updated: Every retrieval operation (frequency++)
├─ Tracks: Query popularity, accuracy, response time, user feedback
└─ Query: Find problematic queries (cold spots, poor accuracy, slow)

HEALING OPERATIONS TABLE
├─ One record per healing operation
├─ Updated: Only when healing is triggered
├─ Tracks: What healing was done, why, what improved
└─ Query: Analyze effectiveness of strategies, total improvement

SYNTHETIC QUERIES TABLE
├─ One record per synthetic question
├─ Multiple rows per document
├─ Updated: During ingestion (INSERT), Testing (UPDATE accuracy)
└─ Query: Get test questions for document quality validation
```

---

## Critical Joins for Analysis

```sql
-- Document quality vs Query accuracy
SELECT 
  em.document_id,
  COUNT(DISTINCT em.chunk_id) as chunk_count,
  AVG(em.quality_score) as avg_embedding_quality,
  dm.doc_id
FROM embedding_metadata em
LEFT JOIN document_metadata dm ON em.document_id = dm.doc_id
GROUP BY em.document_id;

-- Which documents needed the most healing
SELECT 
  DISTINCT dm.doc_id,
  COUNT(DISTINCT ho.healing_id) as healing_count,
  ROUND(AVG(CAST(json_extract(ho.target_docs, '$[0]') AS TEXT)), 4) as improvement
FROM document_metadata dm
LEFT JOIN healing_operations ho 
  ON dm.doc_id IN (SELECT json_each.value FROM json_each(ho.target_docs))
GROUP BY dm.doc_id
ORDER BY healing_count DESC;

-- Query performance improvements from healing
SELECT 
  qh.query_example,
  qh.frequency,
  ROUND(qh.avg_retrieval_accuracy * 100, 2) as current_accuracy,
  COUNT(ho.healing_id) as healing_operations,
  ROUND(SUM(ho.improvement_delta) * 100, 2) as total_improvement
FROM query_heatmap qh
LEFT JOIN healing_operations ho 
  ON datetime(qh.last_queried) > datetime(ho.timestamp)
GROUP BY qh.query_hash
HAVING COUNT(ho.healing_id) > 0
ORDER BY total_improvement DESC;
```

---

## Schema Creation SQL

```sql
-- Create document_metadata table
CREATE TABLE IF NOT EXISTS document_metadata (
  metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
  doc_id TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(doc_id, key)
);

-- Create embedding_metadata table
CREATE TABLE IF NOT EXISTS embedding_metadata (
  embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id TEXT NOT NULL,
  chunk_id TEXT UNIQUE NOT NULL,
  chunk_strategy TEXT DEFAULT 'recursive_splitter',
  chunk_size INTEGER DEFAULT 512,
  overlap INTEGER DEFAULT 50,
  embedding_model TEXT DEFAULT 'ollama',
  embedding_version TEXT,
  quality_score REAL DEFAULT 0.5,
  last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  reindex_count INTEGER DEFAULT 0,
  rbac_namespace TEXT DEFAULT 'general',
  metadata_tags TEXT,  -- JSON
  healing_suggestions TEXT,  -- JSON
  FOREIGN KEY (document_id) REFERENCES document_metadata(doc_id)
);

-- Create query_heatmap table
CREATE TABLE IF NOT EXISTS query_heatmap (
  heatmap_id INTEGER PRIMARY KEY AUTOINCREMENT,
  query_hash TEXT UNIQUE NOT NULL,
  query_example TEXT,
  frequency INTEGER DEFAULT 1,
  avg_retrieval_accuracy REAL DEFAULT 0.5,
  avg_response_time_ms REAL DEFAULT 0.0,
  avg_user_feedback REAL,
  quality_category TEXT DEFAULT 'cold',
  last_queried TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create healing_operations table
CREATE TABLE IF NOT EXISTS healing_operations (
  healing_id INTEGER PRIMARY KEY AUTOINCREMENT,
  strategy TEXT NOT NULL,  -- re_chunk, re_embed, quality_adjustment, etc.
  target_docs TEXT NOT NULL,  -- JSON array of doc_ids
  reason TEXT,
  actions_taken TEXT,  -- JSON
  before_metrics TEXT,  -- JSON
  after_metrics TEXT,  -- JSON
  improvement_delta REAL DEFAULT 0.0,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create synthetic_queries table
CREATE TABLE IF NOT EXISTS synthetic_queries (
  synthetic_id INTEGER PRIMARY KEY AUTOINCREMENT,
  doc_id TEXT NOT NULL,
  question TEXT,
  expected_answer TEXT,
  generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_tested TIMESTAMP,
  test_accuracy REAL,
  FOREIGN KEY (doc_id) REFERENCES document_metadata(doc_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_document_metadata_doc_id 
  ON document_metadata(doc_id);
CREATE INDEX IF NOT EXISTS idx_document_metadata_key 
  ON document_metadata(key);
CREATE INDEX IF NOT EXISTS idx_embedding_metadata_document_id 
  ON embedding_metadata(document_id);
CREATE INDEX IF NOT EXISTS idx_embedding_metadata_quality 
  ON embedding_metadata(quality_score);
CREATE INDEX IF NOT EXISTS idx_query_heatmap_query_hash 
  ON query_heatmap(query_hash);
CREATE INDEX IF NOT EXISTS idx_query_heatmap_accuracy 
  ON query_heatmap(avg_retrieval_accuracy);
CREATE INDEX IF NOT EXISTS idx_healing_operations_strategy 
  ON healing_operations(strategy);
CREATE INDEX IF NOT EXISTS idx_healing_operations_timestamp 
  ON healing_operations(timestamp);
CREATE INDEX IF NOT EXISTS idx_synthetic_queries_doc_id 
  ON synthetic_queries(doc_id);
```

---

## Data Volume Examples

### Small System (1 Document, 10 Queries)
```
document_metadata:        12 rows  (12 fields for 1 doc)
embedding_metadata:       5 rows   (5 chunks)
query_heatmap:           10 rows   (10 unique queries)
healing_operations:       0 rows   (no healing yet)
synthetic_queries:        3 rows   (3 test questions)
────────────────────────────────────
Total:                   30 rows
```

### Medium System (50 Documents, 1000 Queries)
```
document_metadata:      500 rows   (50 docs × 10 fields each)
embedding_metadata:     250 rows   (250 chunks total)
query_heatmap:         1000 rows   (1000 unique queries)
healing_operations:      15 rows   (1-2% of queries need healing)
synthetic_queries:      150 rows   (3 per document)
────────────────────────────────────
Total:                ~1915 rows
```

### Large System (500 Documents, 100K Queries)
```
document_metadata:     5000 rows   (500 docs × 10 fields each)
embedding_metadata:    2500 rows   (5 chunks per doc average)
query_heatmap:       100000 rows   (100000 unique queries)
healing_operations:     500 rows   (0.5% of queries need healing)
synthetic_queries:     1500 rows   (3 per document)
────────────────────────────────────
Total:               ~109500 rows
Size (estimate):     ~50-100 MB
```

---

## Backup & Maintenance

```sql
-- Backup before large operations
.backup './incident_iq_backup_$(date).db'

-- Vacuum to optimize storage
VACUUM;

-- Analyze tables for query optimization
ANALYZE;

-- Check table sizes
SELECT 
  name as table_name,
  COUNT(*) as row_count
FROM (
  SELECT 'document_metadata' as name FROM document_metadata
  UNION ALL
  SELECT 'embedding_metadata' FROM embedding_metadata
  UNION ALL
  SELECT 'query_heatmap' FROM query_heatmap
  UNION ALL
  SELECT 'healing_operations' FROM healing_operations
  UNION ALL
  SELECT 'synthetic_queries' FROM synthetic_queries
)
GROUP BY name;

-- Archive old healing operations (keep last 90 days)
DELETE FROM healing_operations 
WHERE datetime(timestamp) < datetime('now', '-90 days');

-- Archive cold queries (keep last 30 days)
DELETE FROM query_heatmap 
WHERE quality_category = 'cold' 
  AND datetime(last_queried) < datetime('now', '-30 days');
```

---

## Access Patterns

### Most Common Queries (Optimization Priority)

1. **High Frequency**: Get all metadata for a document
   ```sql
   SELECT * FROM document_metadata WHERE doc_id = ?
   -- Index: idx_document_metadata_doc_id ✓
   ```

2. **High Frequency**: Find low-quality chunks
   ```sql
   SELECT * FROM embedding_metadata WHERE quality_score < 0.6
   -- Index: idx_embedding_metadata_quality ✓
   ```

3. **High Frequency**: Check if query exists
   ```sql
   SELECT * FROM query_heatmap WHERE query_hash = ?
   -- Index: idx_query_heatmap_query_hash ✓
   ```

4. **High Frequency**: Update query frequency
   ```sql
   UPDATE query_heatmap SET frequency = frequency + 1 WHERE query_hash = ?
   -- Index: idx_query_heatmap_query_hash ✓
   ```

5. **Batch Operations**: Get most effective healing strategies
   ```sql
   SELECT strategy, AVG(improvement_delta) FROM healing_operations 
   GROUP BY strategy ORDER BY improvement DESC
   -- Index: idx_healing_operations_strategy ✓
   ```

All critical access patterns have corresponding indexes for performance.
