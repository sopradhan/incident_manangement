# SQL Queries to Inspect RAG Metadata Tables

## Quick Reference: Query Your Metadata

### 1. Document Metadata - What was extracted from documents?

```sql
-- All metadata for a specific document
SELECT * FROM document_metadata 
WHERE doc_id = 'doc_incident_001'
ORDER BY key;

-- Get specific metadata value
SELECT value FROM document_metadata 
WHERE doc_id = 'doc_incident_001' AND key = 'title';

-- Count documents ingested
SELECT COUNT(DISTINCT doc_id) as total_documents 
FROM document_metadata;

-- Find all documents with a specific metadata key
SELECT DISTINCT doc_id FROM document_metadata 
WHERE key = 'author'
ORDER BY doc_id;

-- Get all titles and summaries
SELECT DISTINCT 
  dm1.doc_id,
  MAX(CASE WHEN dm1.key = 'title' THEN dm1.value END) as title,
  MAX(CASE WHEN dm1.key = 'summary' THEN dm1.value END) as summary,
  MAX(CASE WHEN dm1.key = 'author' THEN dm1.value END) as author
FROM document_metadata dm1
GROUP BY dm1.doc_id;
```

---

### 2. Embedding Metadata - What chunks exist and their quality?

```sql
-- All chunks for a document with quality scores
SELECT 
  chunk_id,
  chunk_size,
  quality_score,
  embedding_model,
  chunk_strategy,
  last_modified
FROM embedding_metadata
WHERE document_id = 'doc_incident_001'
ORDER BY chunk_id;

-- Find low quality chunks (below 0.6)
SELECT 
  chunk_id,
  document_id,
  quality_score,
  embedding_model,
  healing_suggestions
FROM embedding_metadata
WHERE quality_score < 0.6
ORDER BY quality_score ASC;

-- Get statistics per document
SELECT 
  document_id,
  COUNT(*) as total_chunks,
  AVG(quality_score) as avg_quality,
  MIN(quality_score) as min_quality,
  MAX(quality_score) as max_quality,
  SUM(chunk_size) as total_chars,
  COUNT(DISTINCT embedding_model) as embedding_models_used,
  MAX(reindex_count) as max_reindex_count
FROM embedding_metadata
GROUP BY document_id
ORDER BY avg_quality ASC;

-- Chunks that were re-indexed (healed)
SELECT 
  chunk_id,
  document_id,
  reindex_count,
  chunk_strategy,
  quality_score,
  last_modified
FROM embedding_metadata
WHERE reindex_count > 0
ORDER BY reindex_count DESC, quality_score ASC;

-- Embedding model distribution
SELECT 
  embedding_model,
  COUNT(*) as chunk_count,
  AVG(quality_score) as avg_quality
FROM embedding_metadata
GROUP BY embedding_model;

-- Chunking strategy effectiveness
SELECT 
  chunk_strategy,
  COUNT(*) as total_chunks,
  AVG(chunk_size) as avg_chunk_size,
  AVG(quality_score) as avg_quality,
  ROUND(AVG(quality_score) * 100, 2) as quality_percent
FROM embedding_metadata
GROUP BY chunk_strategy
ORDER BY avg_quality DESC;
```

---

### 3. Query Heatmap - Which queries are popular and accurate?

```sql
-- All queries with full stats
SELECT 
  query_hash,
  query_example,
  frequency,
  ROUND(avg_retrieval_accuracy * 100, 2) as accuracy_percent,
  avg_response_time_ms,
  COALESCE(ROUND(avg_user_feedback, 2), 'N/A') as avg_feedback,
  quality_category,
  last_queried
FROM query_heatmap
ORDER BY frequency DESC;

-- Top 10 most asked queries
SELECT 
  query_hash,
  query_example,
  frequency,
  ROUND(avg_retrieval_accuracy * 100, 2) as accuracy_percent
FROM query_heatmap
ORDER BY frequency DESC
LIMIT 10;

-- Queries with poor performance (accuracy < 70%)
SELECT 
  query_hash,
  query_example,
  frequency,
  ROUND(avg_retrieval_accuracy * 100, 2) as accuracy_percent,
  avg_response_time_ms,
  quality_category
FROM query_heatmap
WHERE avg_retrieval_accuracy < 0.7
ORDER BY avg_retrieval_accuracy ASC;

-- Queries with slow response times
SELECT 
  query_hash,
  query_example,
  frequency,
  avg_response_time_ms,
  ROUND(avg_retrieval_accuracy * 100, 2) as accuracy_percent
FROM query_heatmap
WHERE avg_response_time_ms > 5000
ORDER BY avg_response_time_ms DESC;

-- Quality distribution
SELECT 
  quality_category,
  COUNT(*) as query_count,
  ROUND(AVG(frequency), 2) as avg_frequency,
  ROUND(AVG(avg_retrieval_accuracy) * 100, 2) as avg_accuracy,
  ROUND(AVG(avg_response_time_ms), 2) as avg_response_ms
FROM query_heatmap
GROUP BY quality_category;

-- Queries never asked before (cold start)
SELECT 
  query_hash,
  query_example,
  frequency,
  avg_retrieval_accuracy,
  quality_category
FROM query_heatmap
WHERE frequency = 1 AND quality_category = 'cold'
ORDER BY last_queried DESC;

-- Recent queries (last 24 hours)
SELECT 
  query_hash,
  query_example,
  frequency,
  ROUND(avg_retrieval_accuracy * 100, 2) as accuracy_percent,
  last_queried
FROM query_heatmap
WHERE datetime(last_queried) > datetime('now', '-1 day')
ORDER BY last_queried DESC;

-- User feedback statistics
SELECT 
  COUNT(*) as queries_with_feedback,
  ROUND(AVG(avg_user_feedback), 2) as avg_feedback,
  MIN(avg_user_feedback) as worst_feedback,
  MAX(avg_user_feedback) as best_feedback
FROM query_heatmap
WHERE avg_user_feedback IS NOT NULL;
```

---

### 4. Healing Operations - What optimizations were applied?

```sql
-- All healing operations with results
SELECT 
  healing_id,
  strategy,
  reason,
  improvement_delta,
  timestamp
FROM healing_operations
ORDER BY timestamp DESC;

-- Most effective strategies
SELECT 
  strategy,
  COUNT(*) as times_applied,
  ROUND(AVG(improvement_delta), 4) as avg_improvement,
  ROUND(MAX(improvement_delta), 4) as best_improvement,
  ROUND(MIN(improvement_delta), 4) as worst_improvement
FROM healing_operations
GROUP BY strategy
ORDER BY avg_improvement DESC;

-- Recent optimizations (last 7 days)
SELECT 
  healing_id,
  strategy,
  target_docs,
  reason,
  ROUND(improvement_delta * 100, 2) as improvement_percent,
  timestamp
FROM healing_operations
WHERE datetime(timestamp) > datetime('now', '-7 days')
ORDER BY timestamp DESC;

-- High-impact healing operations (improvement > 20%)
SELECT 
  healing_id,
  strategy,
  target_docs,
  reason,
  ROUND(improvement_delta * 100, 2) as improvement_percent,
  before_metrics,
  after_metrics,
  timestamp
FROM healing_operations
WHERE improvement_delta > 0.2
ORDER BY improvement_delta DESC;

-- Documents that were healed most often
SELECT 
  json_each.value as doc_id,
  COUNT(*) as healing_count,
  ROUND(AVG(improvement_delta), 4) as avg_improvement
FROM healing_operations, json_each(target_docs)
GROUP BY doc_id
ORDER BY healing_count DESC;

-- Total system improvement from healing
SELECT 
  ROUND(SUM(improvement_delta), 4) as total_improvement,
  ROUND(AVG(improvement_delta), 4) as avg_per_operation,
  COUNT(*) as total_operations,
  MIN(timestamp) as first_healing,
  MAX(timestamp) as last_healing
FROM healing_operations;

-- Strategy effectiveness over time
SELECT 
  DATE(timestamp) as healing_date,
  strategy,
  COUNT(*) as applications,
  ROUND(AVG(improvement_delta), 4) as avg_improvement
FROM healing_operations
GROUP BY healing_date, strategy
ORDER BY healing_date DESC, avg_improvement DESC;
```

---

### 5. Synthetic Queries - What test questions were generated?

```sql
-- All synthetic questions for a document
SELECT 
  synthetic_id,
  doc_id,
  question,
  expected_answer,
  test_accuracy,
  generated_date,
  last_tested
FROM synthetic_queries
WHERE doc_id = 'doc_incident_001'
ORDER BY generated_date DESC;

-- Synthetic questions with test results
SELECT 
  doc_id,
  COUNT(*) as total_questions,
  ROUND(AVG(test_accuracy), 4) as avg_accuracy,
  MIN(test_accuracy) as lowest_accuracy,
  MAX(test_accuracy) as highest_accuracy
FROM synthetic_queries
WHERE test_accuracy IS NOT NULL
GROUP BY doc_id
ORDER BY avg_accuracy DESC;

-- Questions never tested
SELECT 
  synthetic_id,
  doc_id,
  question,
  generated_date
FROM synthetic_queries
WHERE test_accuracy IS NULL OR last_tested IS NULL
ORDER BY generated_date DESC;

-- Questions with low accuracy (< 70%)
SELECT 
  synthetic_id,
  doc_id,
  question,
  test_accuracy,
  expected_answer,
  last_tested
FROM synthetic_queries
WHERE test_accuracy IS NOT NULL AND test_accuracy < 0.7
ORDER BY test_accuracy ASC;

-- Recent synthetic questions
SELECT 
  synthetic_id,
  doc_id,
  question,
  COALESCE(ROUND(test_accuracy * 100, 2), 'Not tested') as accuracy_percent,
  generated_date
FROM synthetic_queries
WHERE datetime(generated_date) > datetime('now', '-7 days')
ORDER BY generated_date DESC;
```

---

### 6. Cross-Table Analysis - Correlating Data

```sql
-- Document quality vs query accuracy
SELECT 
  em.document_id,
  COUNT(DISTINCT em.chunk_id) as chunk_count,
  ROUND(AVG(em.quality_score), 4) as avg_embedding_quality,
  COUNT(DISTINCT qh.query_hash) as unique_queries,
  ROUND(AVG(qh.avg_retrieval_accuracy), 4) as avg_query_accuracy
FROM embedding_metadata em
LEFT JOIN query_heatmap qh ON 1=1  -- This would need proper join logic
GROUP BY em.document_id
ORDER BY avg_embedding_quality DESC;

-- Documents that need healing most
SELECT 
  em.document_id,
  ROUND(AVG(em.quality_score), 4) as current_avg_quality,
  COUNT(*) as low_quality_chunks,
  COUNT(DISTINCT ho.healing_id) as healing_operations_applied
FROM embedding_metadata em
LEFT JOIN healing_operations ho ON em.document_id IN (
  SELECT json_each.value FROM json_each(ho.target_docs)
)
WHERE em.quality_score < 0.6
GROUP BY em.document_id
ORDER BY current_avg_quality ASC;

-- Healing impact on query accuracy
SELECT 
  ROUND(AVG(qh.avg_retrieval_accuracy), 4) as avg_query_accuracy_after_healing,
  COUNT(DISTINCT qh.query_hash) as queries_benefited,
  COUNT(DISTINCT ho.healing_id) as healing_ops
FROM query_heatmap qh
CROSS JOIN healing_operations ho
WHERE datetime(qh.last_queried) > datetime(ho.timestamp)
GROUP BY DATE(ho.timestamp)
ORDER BY DATE(ho.timestamp) DESC;
```

---

### 7. Dashboard-Ready Summary Queries

```sql
-- System Health Summary
SELECT 
  'Total Documents' as metric, COUNT(DISTINCT doc_id) as value
FROM document_metadata
UNION ALL
SELECT 'Total Chunks', COUNT(*)
FROM embedding_metadata
UNION ALL
SELECT 'Avg Chunk Quality', ROUND(AVG(quality_score), 4)
FROM embedding_metadata
UNION ALL
SELECT 'Total Queries', COUNT(*)
FROM query_heatmap
UNION ALL
SELECT 'Avg Query Accuracy %', ROUND(AVG(avg_retrieval_accuracy) * 100, 2)
FROM query_heatmap
UNION ALL
SELECT 'Avg Response Time (ms)', ROUND(AVG(avg_response_time_ms), 2)
FROM query_heatmap
UNION ALL
SELECT 'Healing Operations', COUNT(*)
FROM healing_operations
UNION ALL
SELECT 'Total Improvement %', ROUND(SUM(improvement_delta) * 100, 2)
FROM healing_operations;

-- Quality Score Distribution (Histogram)
SELECT 
  CASE 
    WHEN quality_score < 0.2 THEN '0.0-0.2 (Critical)'
    WHEN quality_score < 0.4 THEN '0.2-0.4 (Poor)'
    WHEN quality_score < 0.6 THEN '0.4-0.6 (Fair)'
    WHEN quality_score < 0.8 THEN '0.6-0.8 (Good)'
    ELSE '0.8-1.0 (Excellent)'
  END as quality_bucket,
  COUNT(*) as chunk_count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM embedding_metadata), 2) as percent
FROM embedding_metadata
GROUP BY quality_bucket
ORDER BY quality_score DESC;

-- Retrieval Accuracy Distribution
SELECT 
  CASE 
    WHEN avg_retrieval_accuracy < 0.5 THEN 'Poor (< 50%)'
    WHEN avg_retrieval_accuracy < 0.7 THEN 'Fair (50-70%)'
    WHEN avg_retrieval_accuracy < 0.85 THEN 'Good (70-85%)'
    ELSE 'Excellent (>= 85%)'
  END as accuracy_category,
  COUNT(*) as query_count,
  SUM(frequency) as total_invocations,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM query_heatmap), 2) as percent
FROM query_heatmap
GROUP BY accuracy_category
ORDER BY accuracy_category;
```

---

## Usage Examples in Python

```python
import sqlite3
import json

def get_metadata_summary(db_path='./incident_iq.db'):
    """Get comprehensive metadata summary."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Documents ingested
    cursor.execute("SELECT COUNT(DISTINCT doc_id) as count FROM document_metadata")
    docs = cursor.fetchone()['count']
    
    # Average embedding quality
    cursor.execute("SELECT AVG(quality_score) as avg_quality FROM embedding_metadata")
    quality = cursor.fetchone()['avg_quality']
    
    # Query statistics
    cursor.execute("""
        SELECT 
          COUNT(*) as total_queries,
          AVG(avg_retrieval_accuracy) as avg_accuracy,
          AVG(avg_response_time_ms) as avg_response_time
        FROM query_heatmap
    """)
    query_stats = cursor.fetchone()
    
    # Healing impact
    cursor.execute("SELECT SUM(improvement_delta) as total_improvement FROM healing_operations")
    healing = cursor.fetchone()['total_improvement'] or 0
    
    conn.close()
    
    return {
        'documents_ingested': docs,
        'avg_embedding_quality': quality,
        'total_queries': query_stats['total_queries'],
        'avg_query_accuracy': query_stats['avg_accuracy'],
        'avg_response_time_ms': query_stats['avg_response_time'],
        'total_improvement_from_healing': healing
    }

def get_low_quality_chunks(db_path='./incident_iq.db', threshold=0.6):
    """Get chunks needing healing."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
          chunk_id, document_id, quality_score, healing_suggestions
        FROM embedding_metadata
        WHERE quality_score < ?
        ORDER BY quality_score ASC
    """, (threshold,))
    
    chunks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return chunks
```

---

## Useful Indexes (for performance)

```sql
-- Add indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_document_metadata_doc_id ON document_metadata(doc_id);
CREATE INDEX IF NOT EXISTS idx_document_metadata_key ON document_metadata(key);
CREATE INDEX IF NOT EXISTS idx_embedding_metadata_doc_id ON embedding_metadata(document_id);
CREATE INDEX IF NOT EXISTS idx_embedding_metadata_quality ON embedding_metadata(quality_score);
CREATE INDEX IF NOT EXISTS idx_query_heatmap_query_hash ON query_heatmap(query_hash);
CREATE INDEX IF NOT EXISTS idx_query_heatmap_accuracy ON query_heatmap(avg_retrieval_accuracy);
CREATE INDEX IF NOT EXISTS idx_healing_operations_strategy ON healing_operations(strategy);
CREATE INDEX IF NOT EXISTS idx_healing_operations_timestamp ON healing_operations(timestamp);
CREATE INDEX IF NOT EXISTS idx_synthetic_queries_doc_id ON synthetic_queries(doc_id);
```
