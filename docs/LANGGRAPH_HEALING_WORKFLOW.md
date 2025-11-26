# LangGraph RAG Agent - Intelligent Healing Workflow

## Complete Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DOCUMENT INGESTION PHASE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Input: Raw Document Text (Incidents, Procedures, Guidelines, etc) │
│                           │                                          │
│                           ▼                                          │
│            ┌────────────────────────────┐                            │
│            │ extract_metadata_tool      │                            │
│            │ - Title extraction         │                            │
│            │ - Author identification    │                            │
│            │ - Keywords extraction      │                            │
│            │ - Summary generation       │                            │
│            └────────────────┬───────────┘                            │
│                             │                                         │
│            ┌────────────────▼───────────┐                            │
│            │ chunk_document_tool        │                            │
│            │ - Recursive text splitting │                            │
│            │ - Configurable chunk_size │                            │
│            │ - Overlap setting          │                            │
│            └────────────────┬───────────┘                            │
│                             │                                         │
│            ┌────────────────▼───────────┐                            │
│            │ save_to_vectordb_tool      │                            │
│            │ - Generate embeddings      │──► ChromaDB               │
│            │ - Save to vector store     │    (PersistentClient)    │
│            └────────────────┬───────────┘                            │
│                             │                                         │
│            ┌────────────────▼───────────┐                            │
│            │ update_metadata_tracking   │                            │
│            │ - Finalize doc metadata    │                            │
│            └────────────────┬───────────┘                            │
│                             │                                         │
│          ┌──────────────────┼──────────────────┬──────────────────┐  │
│          ▼                  ▼                  ▼                  ▼  │
│  document_metadata  embedding_metadata  synthetic_queries   metadata_id
│  ✓ title            ✓ chunk_id          ✓ test questions           │
│  ✓ author           ✓ quality_score     ✓ expected_answers         │
│  ✓ source           ✓ chunk_strategy                               │
│  ✓ summary          ✓ embedding_model                              │
│  ✓ keywords         ✓ reindex_count                                │
│                     ✓ rbac_namespace                               │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Retrieval Phase with Intelligent Healing

```
┌─────────────────────────────────────────────────────────────────────┐
│               RETRIEVAL PHASE - INTELLIGENT HEALING                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Input: User Question                                                │
│         [Optional] Performance History                               │
│                           │                                          │
│                           ▼                                          │
│            ┌────────────────────────────┐                            │
│            │ retrieve_context_tool      │                            │
│            │ - Generate query embedding │                            │
│            │ - Vector similarity search │                            │
│            │ - Top-k retrieval (k=5)    │──► ChromaDB              │
│            │ - Calculate quality metric │                            │
│            └────────────────┬───────────┘                            │
│                             │                                         │
│                retrieval_quality = docs_found / expected             │
│                             │                                         │
│            ┌────────────────▼───────────┐                            │
│            │ rerank_context_tool        │                            │
│            │ - Sort by relevance        │                            │
│            │ - Filter duplicates        │                            │
│            │ - Final context prep       │                            │
│            └────────────────┬───────────┘                            │
│                             │                                         │
│            ┌────────────────▼─────────────────┐                      │
│            │ check_optimization_needed (KEY)  │                      │
│            │                                  │                      │
│            │ Decision Logic:                  │                      │
│            │ ─────────────────                │                      │
│            │ IF quality < 0.6     → OPTIMIZE  │                      │
│            │ IF results < 3       → OPTIMIZE  │                      │
│            │ IF history exists    → OPTIMIZE  │                      │
│            │ ELSE                 → SKIP      │                      │
│            └────┬───────────────────┬────────┘                       │
│                 │ should_optimize   │                                │
│                 │ = TRUE/FALSE      │                                │
│                 │                   │                                │
│   ╔═════════════╩═════════════════════════════════════╗              │
│   ║                                                   ║              │
│   ▼ YES (Healing Needed)                     ▼ NO (Skip)            │
│   │                                              │                   │
│   │  ┌──────────────────────────┐               │                   │
│   │  │ get_context_cost_tool    │               │                   │
│   │  │ - Count tokens           │               │                   │
│   │  │ - Estimate cost (USD)    │               │                   │
│   │  │ - Get model rates        │               │                   │
│   │  └──────────┬───────────────┘               │                   │
│   │             │                               │                   │
│   │  ┌──────────▼───────────────┐               │                   │
│   │  │ optimize_chunk_size_tool │               │                   │
│   │  │ - Analyze history        │               │                   │
│   │  │ - Suggest new k value    │               │                   │
│   │  │ - Suggest chunk_size     │               │                   │
│   │  │ - Generate recommendation│               │                   │
│   │  └──────────┬───────────────┘               │                   │
│   │             │                               │                   │
│   │        ┌────▼──────────────┐                │                   │
│   │        │ optimization_result                │                   │
│   │        │ - cost_analysis   │                │                   │
│   │        │ - suggested_params│                │                   │
│   │        │ - tokens_before   │                │                   │
│   │        └──────┬────────────┘                │                   │
│   │               │                             │                   │
│   └───────────────┼─────────────────────────────┘                   │
│                   │                                                  │
│            ┌──────▼──────────────┐                                   │
│            │ answer_question_tool│                                   │
│            │ - Generate final    │                                   │
│            │   answer using LLM  │                                   │
│            └────────┬────────────┘                                   │
│                     │                                                │
│            ┌────────▼──────────────┐                                 │
│            │ traceability_tool     │                                 │
│            │ - Source attribution  │                                 │
│            │ - Similarity scores   │                                 │
│            │ - Document IDs        │                                 │
│            └────────┬──────────────┘                                 │
│                     │                                                │
│                 ┌───▼──────────┐                                     │
│                 │ query_heatmap│                                     │
│                 │ - frequency++│                                     │
│                 │ - accuracy   │                                     │
│                 │ - response_t │                                     │
│                 │ - feedback   │                                     │
│                 └──────────────┘                                     │
│                     │                                                │
│                     ▼                                                │
│            Final Answer + Sources + Traceability                    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## SQLite Tables Update Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                  SQLITE METADATA TRACKING                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  INGESTION UPDATES:                                                  │
│  ────────────────                                                    │
│  extract_metadata        ──► document_metadata                       │
│  ├─ doc_id               ├─ metadata_id (PRIMARY KEY)               │
│  ├─ title                ├─ doc_id (FOREIGN KEY)                    │
│  ├─ author               ├─ key (title, author, source, etc)        │
│  ├─ source               └─ value (extracted value)                 │
│  └─ keywords                                                         │
│                                                                       │
│  save_to_vectordb        ──► embedding_metadata                     │
│  ├─ chunks               ├─ embedding_id (PRIMARY KEY)              │
│  ├─ doc_id               ├─ document_id (FOREIGN KEY)               │
│  ├─ embeddings           ├─ chunk_id                                │
│  └─ metadata             ├─ quality_score (initial: 0.5)            │
│                          ├─ chunk_strategy (recursive_splitter)     │
│                          ├─ chunk_size (512, 1024, etc)             │
│                          ├─ overlap (percentage)                    │
│                          ├─ embedding_model (ollama, etc)           │
│                          ├─ embedding_version                       │
│                          ├─ last_modified                           │
│                          ├─ reindex_count (starts at 0)             │
│                          └─ healing_suggestions                     │
│                                                                       │
│  extract_metadata        ──► synthetic_queries                      │
│  └─ Generated questions   ├─ synthetic_id (PRIMARY KEY)             │
│                          ├─ doc_id (FOREIGN KEY)                    │
│                          ├─ question (auto-generated)               │
│                          ├─ expected_answer                         │
│                          └─ generated_date                          │
│                                                                       │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                       │
│  RETRIEVAL UPDATES (Every Query):                                    │
│  ──────────────────────────────                                      │
│  ask_question            ──► query_heatmap                          │
│  ├─ question             ├─ heatmap_id (PRIMARY KEY)                │
│  ├─ context retrieved    ├─ query_hash                              │
│  ├─ response time        ├─ query_example                           │
│  ├─ answer generated     ├─ frequency++ (incremented)               │
│  └─ user feedback        ├─ avg_retrieval_accuracy                  │
│                          ├─ avg_response_time_ms                    │
│                          ├─ avg_user_feedback                       │
│                          ├─ quality_category (cold/warm/hot)        │
│                          └─ last_queried (updated)                  │
│                                                                       │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                       │
│  OPTIMIZATION/HEALING UPDATES (When Healing Triggered):              │
│  ────────────────────────────────────────────────────               │
│  optimize_chunk_size_tool ──► healing_operations                    │
│  ├─ suggested params      ├─ healing_id (PRIMARY KEY)               │
│  ├─ improvement metrics   ├─ strategy (re_chunk, re_embed)          │
│  └─ cost analysis         ├─ target_docs (JSON list)                │
│                          ├─ reason (quality < 0.6, etc)             │
│                          ├─ actions_taken (JSON)                    │
│                          ├─ before_metrics (JSON)                   │
│                          ├─ after_metrics (JSON)                    │
│                          ├─ improvement_delta (percentage)          │
│                          └─ timestamp                               │
│                                                                       │
│  Apply suggestions       ──► embedding_metadata (UPDATE)            │
│                          ├─ quality_score (improved)                │
│                          ├─ chunk_size (new size)                   │
│                          ├─ overlap (new overlap)                   │
│                          ├─ reindex_count++ (incremented)           │
│                          ├─ healing_suggestions (updated)           │
│                          └─ last_modified (now)                     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Decision Logic: When to Trigger Healing

```python
# In LangGraph's check_optimization_needed node:

should_optimize = (
    # Condition 1: Quality Metric
    quality < 0.6                                    # < 60% quality
    
    OR
    
    # Condition 2: Insufficient Results
    len(reranked_context) < 3                        # Too few chunks
    
    OR
    
    # Condition 3: Performance Trend Analysis
    (performance_history is not None 
     and len(performance_history) > 2)              # Enough history to analyze
)

if should_optimize:
    # Execute healing workflow
    1. get_context_cost_tool()
       └─ Calculate token count and cost
    
    2. optimize_chunk_size_tool()
       └─ Suggest better parameters based on history
    
    3. update healing_operations table
       └─ Log the optimization attempt
    
    # Then continue with answer generation
else:
    # Skip healing, go directly to answer
    1. answer_question_tool()
    2. traceability_tool()
```

---

## Data State Through Pipeline

```
Query: "What are incident severity levels?"

┌─────────────────────────────────────────────────────────────────┐
│ Step 1: retrieve_context_tool                                  │
├─────────────────────────────────────────────────────────────────┤
│ State {                                                          │
│   "question": "What are incident severity levels?",             │
│   "context": {                                                   │
│     "success": true,                                            │
│     "context": [                                                │
│       {                                                          │
│         "text": "Severity Level 1 - Critical...",               │
│         "score": 0.92,                                          │
│         "metadata": {"doc_id": "doc_001", ...}                 │
│       },                                                         │
│       ...                                                        │
│     ]                                                            │
│   },                                                             │
│   "retrieval_quality": 1.0  # 5/5 docs found                    │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: rerank_context_tool                                    │
├─────────────────────────────────────────────────────────────────┤
│ State {                                                          │
│   ...,                                                           │
│   "reranked_context": {                                          │
│     "success": true,                                            │
│     "reranked_context": [                                       │
│       # Same docs, sorted by score DESC                         │
│       {                                                          │
│         "text": "Severity Level 1...",                          │
│         "score": 0.95,                                          │
│         "metadata": {...}                                       │
│       },                                                         │
│       ...                                                        │
│     ]                                                            │
│   }                                                              │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: check_optimization_needed                              │
├─────────────────────────────────────────────────────────────────┤
│ State {                                                          │
│   ...,                                                           │
│   "should_optimize": false,  # quality=1.0 > 0.6               │
│   "optimization_reason": "Quality sufficient"                   │
│ }                                                                │
│                                                                  │
│ ──► ROUTE: Skip healing → Go to answer_question                │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: answer_question_tool                                   │
├─────────────────────────────────────────────────────────────────┤
│ State {                                                          │
│   ...,                                                           │
│   "answer": "There are four severity levels...",                │
│   "status": "answer_generated"                                  │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: traceability_tool                                       │
├─────────────────────────────────────────────────────────────────┤
│ State {                                                          │
│   ...,                                                           │
│   "traceability": {                                              │
│     "success": true,                                            │
│     "traceability": {                                            │
│       "question": "What are...",                                │
│       "sources_used": 5,                                        │
│       "documents": [                                             │
│         {                                                        │
│           "doc_id": "doc_001",                                  │
│           "chunk_index": 0,                                     │
│           "similarity_score": 0.95,                             │
│           "text_preview": "Severity Level 1..."                 │
│         },                                                       │
│         ...                                                      │
│       ]                                                          │
│     }                                                            │
│   },                                                             │
│   "status": "completed"                                         │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
                            ▼
                     FINAL RESPONSE:
                     {
                       "answer": "There are four...",
                       "sources": [5 documents],
                       "traceability": {...},
                       "optimization_applied": false,
                       "retrieval_quality": 1.0
                     }

     UPDATED TABLES:
     • query_heatmap → frequency++, accuracy=high, response_time recorded
```

---

## Performance Metrics Captured

### Per-Query Metrics
- **Query Hash**: Hash of the question
- **Frequency**: How often asked
- **Retrieval Accuracy**: % of relevant docs retrieved
- **Response Time**: ms to generate answer
- **User Feedback**: 1-5 score (if provided)
- **Quality Category**: cold (rare), warm (medium), hot (frequent)

### Per-Document Metrics
- **Chunk Count**: Total chunks in document
- **Avg Quality Score**: Average chunk quality
- **Reindex Count**: Times re-indexed/healed
- **Healing Suggestions**: Auto-generated tips

### System-Wide Metrics
- **Total Queries**: Cumulative query count
- **Avg Accuracy**: System-wide accuracy
- **Most Problematic Queries**: Low accuracy, high response time
- **Most Effective Strategies**: Healing methods with best results
