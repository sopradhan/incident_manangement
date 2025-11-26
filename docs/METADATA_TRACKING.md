# Metadata Tracking in RAG System

## SQLite Tables Updated During RAG Operations

### 1. **document_metadata** Table
**Purpose:** Stores document-level metadata extracted during ingestion

**Columns:**
- `metadata_id` (INTEGER PRIMARY KEY)
- `doc_id` (TEXT) - Document identifier
- `key` (TEXT) - Metadata key name
- `value` (TEXT) - Metadata value

**Updated During:**
- Document ingestion (via `update_metadata_tracking_tool`)
- Stores extracted title, author, source, date, summary, etc.

**Example Data:**
```
doc_id='doc_001', key='title', value='Incident Management Best Practices'
doc_id='doc_001', key='author', value='Security Team'
doc_id='doc_001', key='source', value='knowledge_base'
doc_id='doc_001', key='summary', value='Guidelines for handling security incidents'
```

---

### 2. **embedding_metadata** Table
**Purpose:** Tracks embedding and chunking information for quality control

**Columns:**
- `embedding_id` (INTEGER PRIMARY KEY)
- `document_id` (TEXT) - Document identifier
- `chunk_id` (TEXT) - Unique chunk identifier
- `chunk_strategy` (TEXT) - Strategy used (e.g., 'recursive_splitter')
- `chunk_size` (INTEGER) - Size of chunk in characters
- `overlap` (INTEGER) - Overlap between chunks
- `embedding_model` (TEXT) - Model used for embeddings
- `embedding_version` (TEXT) - Version of embedding model
- `quality_score` (FLOAT) - Quality score (0.0-1.0)
- `last_modified` (TIMESTAMP) - Last update timestamp
- `reindex_count` (INTEGER) - Number of times reindexed
- `rbac_namespace` (TEXT) - RBAC namespace for the chunk
- `metadata_tags` (TEXT) - JSON tags
- `healing_suggestions` (TEXT) - Suggestions for improvement

**Updated During:**
- Document ingestion (chunks and embedding metadata saved)
- Healing operations (quality_score, healing_suggestions updated)
- Optimization workflow (chunk_size, overlap, reindex_count updated)

**Example Data:**
```
document_id='doc_001', chunk_id='doc_001_chunk_0', chunk_size=512, quality_score=0.85,
embedding_model='ollama', reindex_count=0, chunk_strategy='recursive_splitter'
```

---

### 3. **query_heatmap** Table
**Purpose:** Tracks query patterns and retrieval performance

**Columns:**
- `heatmap_id` (INTEGER PRIMARY KEY)
- `query_hash` (TEXT) - Hash of the query
- `query_example` (TEXT) - Example query text
- `frequency` (INTEGER) - How often this query or similar is asked
- `avg_retrieval_accuracy` (FLOAT) - Average accuracy of retrieval
- `avg_response_time_ms` (INTEGER) - Average response time
- `avg_user_feedback` (FLOAT) - Average user feedback score
- `quality_category` (TEXT) - Category (cold/warm/hot)
- `last_queried` (TIMESTAMP) - Last query timestamp

**Updated During:**
- Every retrieval operation
- Used by healing agent to identify problematic queries
- Helps optimize the system based on actual usage patterns

**Example Data:**
```
query_hash='abc123', query_example='What is incident severity?',
frequency=42, avg_retrieval_accuracy=0.92, avg_response_time_ms=250,
quality_category='warm'
```

---

### 4. **healing_operations** Table
**Purpose:** Logs all healing/optimization operations performed

**Columns:**
- `healing_id` (INTEGER PRIMARY KEY)
- `strategy` (TEXT) - Healing strategy used (e.g., 're_embed', 're_chunk')
- `target_docs` (TEXT) - JSON list of document IDs targeted
- `reason` (TEXT) - Why healing was applied
- `actions_taken` (TEXT) - JSON of actions performed
- `before_metrics` (TEXT) - JSON of metrics before healing
- `after_metrics` (TEXT) - JSON of metrics after healing
- `improvement_delta` (FLOAT) - Improvement percentage
- `timestamp` (TIMESTAMP) - When healing was applied

**Updated During:**
- Optimization workflow execution
- Healing agent identifies and applies fixes
- Tracks all optimization history

**Example Data:**
```
strategy='re_chunk', target_docs='["doc_001", "doc_002"]',
reason='Quality score below 0.6', improvement_delta=0.15,
before_metrics='{"avg_quality": 0.55}', after_metrics='{"avg_quality": 0.70}'
```

---

### 5. **synthetic_queries** Table
**Purpose:** Stores synthetically generated questions for testing and evaluation

**Columns:**
- `synthetic_id` (INTEGER PRIMARY KEY)
- `doc_id` (TEXT) - Document ID the question targets
- `question` (TEXT) - Synthetically generated question
- `expected_answer` (TEXT) - Expected answer
- `generated_date` (TIMESTAMP) - When generated
- `last_tested` (TIMESTAMP) - Last test run
- `test_accuracy` (FLOAT) - Accuracy on last test

**Updated During:**
- Ingestion workflow (synthetic questions generated)
- Healing workflow (used for quality testing)
- Optimization (accuracy results stored)

---

## Data Flow: Ingestion to Optimization

```
1. INGESTION PHASE
   ├─ extract_metadata_tool
   │  └─ Updates: document_metadata (stores title, author, source, etc.)
   │
   ├─ chunk_document_tool
   │  └─ Prepares chunks for embedding
   │
   ├─ save_to_vectordb_tool
   │  ├─ Saves embeddings to ChromaDB
   │  └─ Updates: embedding_metadata (stores chunk info, embedding model, quality score)
   │
   └─ update_metadata_tracking_tool
      └─ Updates: document_metadata (stores final ingestion tracking)

2. RETRIEVAL PHASE
   ├─ retrieve_context_tool
   │  └─ Executes vector search
   │
   ├─ rerank_context_tool
   │  └─ Reranks by relevance
   │
   ├─ check_optimization_needed (INTELLIGENT DECISION)
   │  ├─ Evaluates retrieval quality
   │  ├─ Checks result count
   │  └─ Analyzes performance history
   │
   ├─ IF OPTIMIZATION NEEDED:
   │  ├─ get_context_cost_tool
   │  │  └─ Calculates token cost
   │  │
   │  └─ optimize_chunk_size_tool
   │     └─ Suggests parameter changes
   │
   ├─ answer_question_tool
   │  └─ Generates answer
   │
   ├─ traceability_tool
   │  └─ Provides source attribution
   │
   └─ Updates: query_heatmap (stores query metrics)

3. OPTIMIZATION/HEALING PHASE
   ├─ Apply suggested parameters
   ├─ Re-chunk or re-embed documents
   ├─ Update embedding_metadata with new parameters
   ├─ Update healing_operations table with results
   └─ Store performance improvements
```

---

## Example: Complete Query Lifecycle

### Step 1: Ingestion
```python
agent.ingest_document(text="Incident severity levels...", doc_id="doc_001")
```

**Tables Updated:**
- `document_metadata`: title, author, summary, source
- `embedding_metadata`: chunks created, quality scores, embedding model info
- `synthetic_queries`: test questions generated

---

### Step 2: Retrieval with Intelligent Optimization
```python
result = agent.ask_question("What are incident severity levels?")
```

**Tables Updated:**
- `query_heatmap`: query recorded with accuracy, response time
- `embedding_metadata`: if healing applied, quality scores updated
- `healing_operations`: if optimization was triggered, logged here

---

### Step 3: Performance Tracking
Query can be re-executed with performance history to show improvements:

```python
perf_history = [
    {"params": {"k": 5, "chunk_size": 512}, "metrics": {"cost": 0.001, "accuracy": 0.85}},
    {"params": {"k": 4, "chunk_size": 256}, "metrics": {"cost": 0.0008, "accuracy": 0.88}}
]

result = agent.ask_question("What are incident severity levels?", 
                           performance_history=perf_history)
```

---

## Metadata Fields Tracked

### Document Metadata (document_metadata table)
- **title** - Document title/name
- **author** - Author/creator
- **source** - Source URL or system
- **created_date** - Creation timestamp
- **summary** - Brief summary
- **categories** - Document categories
- **keywords** - Searchable keywords
- **doc_type** - Type of document (guide, procedure, etc.)

### Embedding Metadata (embedding_metadata table)
- **chunk_strategy** - How document was chunked
- **chunk_size** - Size in characters
- **overlap** - Overlap percentage
- **embedding_model** - LLM model used
- **embedding_version** - Model version
- **quality_score** - 0-1 score
- **reindex_count** - Times re-indexed
- **rbac_namespace** - Access control tag
- **healing_suggestions** - Auto-generated improvement tips

### Query Performance (query_heatmap table)
- **query_hash** - Unique query identifier
- **frequency** - Usage count
- **avg_retrieval_accuracy** - Average accuracy %
- **avg_response_time_ms** - Response time
- **avg_user_feedback** - User satisfaction
- **quality_category** - cold/warm/hot status

### Healing Operations (healing_operations table)
- **strategy** - Optimization type applied
- **target_docs** - Documents affected
- **reason** - Why optimization triggered
- **improvement_delta** - % improvement achieved
- **before/after_metrics** - Performance comparison

---

## Accessing Metadata Programmatically

```python
from incident_iq.database.models.document_metadata_model import DocumentMetadataModel
from incident_iq.database.models.embedding_model import EmbeddingMetadataModel
from incident_iq.database.models.tracking_model import QueryHeatmapModel, HealingOperationModel

# Get document metadata
meta_model = DocumentMetadataModel()
meta_model.get_all_metadata(document_id="doc_001")

# Get embedding quality stats
emb_model = EmbeddingMetadataModel()
stats = emb_model.get_embedding_stats()
low_quality = emb_model.get_low_quality_chunks(threshold=0.6)

# Get query performance
heatmap_model = QueryHeatmapModel()
analysis = heatmap_model.get_heatmap_analysis()
stats = heatmap_model.get_stats()

# Get healing operations
healing_model = HealingOperationModel()
most_effective = healing_model.get_most_effective_strategies()
improvement = healing_model.get_total_improvement()
```

---

## Intelligent Healing Integration in LangGraph

The LangGraph retrieval workflow now intelligently decides when to apply healing:

```
Retrieval Flow:
1. retrieve_context
   ├─ Calculate retrieval_quality = (docs_found / expected) * 100
   │
2. rerank_context
   │
3. check_optimization_needed (DECISION NODE)
   ├─ IF quality < 60% → optimize
   ├─ IF results < 3 → optimize
   ├─ IF performance_history > 2 entries → optimize
   │
4. CONDITIONAL ROUTING:
   ├─ YES: optimize_context
   │  ├─ Call get_context_cost_tool → analyze token usage
   │  ├─ Call optimize_chunk_size_tool → suggest parameters
   │  └─ Log to healing_operations table
   │
   └─ NO: skip directly to answer_question
   
5. answer_question
   
6. traceability (with source attribution)
```

---

## Performance Metrics Tracked

### Per-Query Metrics
- Response time (ms)
- Tokens used
- Number of chunks retrieved
- Retrieval accuracy
- User satisfaction score

### Per-Document Metrics
- Average chunk quality score
- Reindex count
- Total embeddings count
- Healing operations applied
- Performance improvement %

### System-Wide Metrics
- Total queries processed
- Average accuracy across all queries
- Cost per query
- Most problematic queries (cold spots)
- Most effective healing strategies
