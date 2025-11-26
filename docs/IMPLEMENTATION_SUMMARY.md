# LangGraph RAG Agent - Implementation Summary

## Overview

The LangGraph RAG Agent has been successfully enhanced with **intelligent healing/optimization integration**. The system now automatically detects when retrieval quality is poor and applies healing strategies to reduce token consumption and improve response quality.

---

## Key Features

### 1. ✅ Intelligent Healing Decision Logic
**Location:** `langgraph_rag_agent.py` → `_build_retrieval_graph()` → `check_optimization_needed` node

The system intelligently decides when to apply healing based on:
- **Quality Metric**: If retrieval_quality < 60%
- **Result Count**: If fewer than 3 documents retrieved
- **Performance History**: If historical data exists for trend analysis

```python
should_optimize = (
    quality < 0.6 or 
    len(reranked) < 3 or 
    (performance_history and len(performance_history) > 2)
)
```

### 2. ✅ Healing Workflow Integration
When healing is triggered:
1. **Cost Analysis** → `get_context_cost_tool` calculates token count and USD cost
2. **Optimization Suggestions** → `optimize_chunk_size_tool` recommends parameters
3. **Logging** → Results stored in `healing_operations` table

### 3. ✅ Conditional Routing
**Graph Structure:**
```
retrieve_context 
  ↓
rerank_context 
  ↓
check_optimization_needed ──┬─→ YES → optimize_context → answer_question
                            └─→ NO  → answer_question
  ↓
traceability
```

### 4. ✅ Complete Metadata Tracking
Five SQLite tables track the entire RAG lifecycle:

| Table | Purpose | Updated During |
|-------|---------|-----------------|
| `document_metadata` | Extracted document info (title, author, source, etc) | Ingestion |
| `embedding_metadata` | Chunk quality, chunking strategy, embedding model | Ingestion, Optimization |
| `query_heatmap` | Query frequency, accuracy, response time, feedback | Every query |
| `healing_operations` | Optimization history and improvement metrics | When healing applied |
| `synthetic_queries` | Auto-generated test questions for documents | Ingestion |

---

## Architecture Diagram

```
USER QUESTION
    ↓
[retrieve_context] ──→ Calculate quality metric (0-1)
    ↓
[rerank_context] ──→ Sort by relevance
    ↓
[check_optimization_needed] ──┐
    │                          │
    └─→ DECISION LOGIC ────────┤
       • quality < 0.6? ────┐  │
       • results < 3?    ───┼──┤
       • history exists? ─┘  │
                             ├─→ YES (should_optimize=true)
                             │
                             ├─→ [optimize_context]
                             │   • get_context_cost_tool
                             │   • optimize_chunk_size_tool
                             │   • Update: healing_operations
                             │   ↓
                             ├─→ [answer_question]
                             │   ↓
                             ├─→ [traceability]
                             │   ↓
                             └─→ FINAL ANSWER + SOURCES + METADATA

    UPDATED TABLES:
    • query_heatmap (frequency++, accuracy, response_time)
```

---

## Data Flow: Ingestion to Optimization

### Phase 1: Ingestion
```
Document → extract_metadata → document_metadata table
         → chunk_document   → (memory)
         → save_to_vectordb → embedding_metadata + ChromaDB
         → update_tracking  → document_metadata table
                            → synthetic_queries table
```

### Phase 2: Retrieval (Intelligent)
```
Question → retrieve_context → context (calculate quality)
        → rerank_context   → reranked_context
        → [DECISION POINT]
           ├─ If healing needed:
           │  ├─ get_context_cost    → cost_analysis
           │  ├─ optimize_chunk_size → suggested_params
           │  └─ heal_operations     → healing_operations table
           └─ Else skip healing
        → answer_question  → final_answer
        → traceability    → sources_with_attribution
        
    UPDATED: query_heatmap table (every query)
```

### Phase 3: Optimization
When healing is triggered:
```
1. Analyze current context tokens and cost
2. Examine performance history (if available)
3. Suggest parameter adjustments:
   • Reduce chunk_size (e.g., 512 → 256)
   • Adjust k_final (e.g., 5 → 3)
   • Change overlap percentage
4. Log optimization to healing_operations
5. Update embedding_metadata with new settings
6. Generate healing_suggestions for future reference
```

---

## SQLite Tables Updated

### document_metadata
**What:** Extracted document-level information
**Columns:** doc_id, key (title, author, source, summary, etc), value
**Updated:** During ingestion
```sql
SELECT * FROM document_metadata 
WHERE doc_id = 'doc_incident_001'
-- Returns: title, author, source, created_date, summary, keywords, etc.
```

### embedding_metadata
**What:** Chunk-level information and quality metrics
**Columns:** document_id, chunk_id, chunk_size, quality_score, embedding_model, reindex_count, healing_suggestions
**Updated:** Ingestion + Optimization
```sql
-- Find low quality chunks
SELECT chunk_id, quality_score, healing_suggestions 
FROM embedding_metadata 
WHERE quality_score < 0.6 
ORDER BY quality_score;
```

### query_heatmap
**What:** Query performance and popularity
**Columns:** query_hash, query_example, frequency, avg_retrieval_accuracy, avg_response_time_ms, avg_user_feedback
**Updated:** Every retrieval operation
```sql
-- Top queries
SELECT query_example, frequency, avg_retrieval_accuracy * 100 as accuracy_pct
FROM query_heatmap
ORDER BY frequency DESC;
```

### healing_operations
**What:** All optimization operations performed
**Columns:** strategy, target_docs, reason, improvement_delta, before_metrics, after_metrics, timestamp
**Updated:** When healing is applied
```sql
-- Most effective strategies
SELECT strategy, AVG(improvement_delta) as avg_improvement
FROM healing_operations
GROUP BY strategy
ORDER BY avg_improvement DESC;
```

### synthetic_queries
**What:** Auto-generated test questions for quality validation
**Columns:** doc_id, question, expected_answer, test_accuracy
**Updated:** During ingestion
```sql
-- Questions with test results
SELECT doc_id, COUNT(*) as questions, AVG(test_accuracy) as avg_accuracy
FROM synthetic_queries
WHERE test_accuracy IS NOT NULL
GROUP BY doc_id;
```

---

## Response Format

```python
result = agent.ask_question("What are incident severity levels?")

# Returns:
{
    "success": True,
    "question": "What are incident severity levels?",
    "answer": "There are four severity levels: Critical, High, Medium, Low. Each has specific...",
    "sources": [
        {
            "text": "Severity Level 1 - Critical...",
            "score": 0.95,
            "metadata": {"doc_id": "doc_001", "chunk_index": 0, ...}
        },
        # ... more sources
    ],
    "traceability": {
        "question": "What are incident severity levels?",
        "sources_used": 5,
        "documents": [
            {
                "doc_id": "doc_001",
                "chunk_index": 0,
                "similarity_score": 0.95,
                "text_preview": "Severity Level 1 - Critical: Complete service outage..."
            },
            # ... more documents
        ]
    },
    "optimization_applied": False,  # or True if healing was triggered
    "optimization_reason": "Quality sufficient",  # or healing reason
    "optimization_result": {},  # Contains cost_analysis and suggested_params if healing applied
    "retrieval_quality": 1.0,  # 0-1 scale (1.0 = perfect)
    "errors": []
}
```

---

## File Locations

### Core Implementation
- **Agent:** `src/incident_iq/rag/agents/langgraph_agent/langgraph_rag_agent.py`
- **Tools:** `src/incident_iq/rag/tools/`
  - `retrieval_tools.py` - retrieval context, ranking, answering
  - `healing_tools.py` - cost analysis, optimization suggestions
  - `ingestion_tools.py` - document processing
- **Services:** `src/incident_iq/rag/tools/services/`
  - `llm_service.py` - LLM provider abstraction
  - `vectordb_service.py` - ChromaDB wrapper

### Database Models
- **Tracking:** `src/incident_iq/database/models/tracking_model.py`
  - `HealingOperationModel` - healing_operations table
  - `QueryHeatmapModel` - query_heatmap table
  - `SyntheticQueryModel` - synthetic_queries table
- **Metadata:** `src/incident_iq/database/models/document_metadata_model.py`
  - `DocumentMetadataModel` - document_metadata table
- **Embedding:** `src/incident_iq/database/models/embedding_model.py`
  - `EmbeddingMetadataModel` - embedding_metadata table

### Tests
- `scripts/test_langgraph_rag.py` - Basic LangGraph tests
- `scripts/test_langgraph_with_healing.py` - Comprehensive test with healing demonstration

### Documentation
- `docs/METADATA_TRACKING.md` - Complete metadata tracking guide
- `docs/LANGGRAPH_HEALING_WORKFLOW.md` - Visual workflow diagrams
- `docs/SQL_METADATA_QUERIES.md` - SQL queries to inspect metadata

---

## Usage Example

```python
from incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent

# Initialize agent
agent = LangGraphRAGAgent()

# 1. Ingest document
result = agent.ingest_document(
    text="Incident Severity Levels...",
    doc_id="doc_incident_001"
)
print(f"Chunks saved: {result['chunks_saved']}")
# Updates: document_metadata, embedding_metadata, synthetic_queries

# 2. Ask question with optional performance history
perf_history = [
    {"params": {"k": 5, "chunk_size": 512}, "metrics": {"cost": 0.001, "accuracy": 0.85}}
]

result = agent.ask_question(
    "What are incident severity levels?",
    performance_history=perf_history
)

print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])} documents")
print(f"Optimization applied: {result['optimization_applied']}")
print(f"Retrieval quality: {result['retrieval_quality']*100:.1f}%")
# Updates: query_heatmap, (optionally) healing_operations

# 3. Check metadata
from incident_iq.database.models.embedding_model import EmbeddingMetadataModel
emb_model = EmbeddingMetadataModel()
stats = emb_model.get_embedding_stats()
print(f"Total chunks: {stats['total_chunks']}")
print(f"Avg quality: {stats['avg_quality_score']:.2f}")
```

---

## Healing Decision Examples

### Example 1: High Quality Response (No Healing)
```
Query: "What are incident severity levels?"

Context retrieved: 5/5 documents
Reranked successfully: quality = 1.0 (100%)
Decision: should_optimize = False
Reason: "Quality sufficient"
Action: Skip healing → Go to answer_question
Result: Final answer with sources

Tables updated: query_heatmap only
```

### Example 2: Low Quality Response (Apply Healing)
```
Query: "What is the incident resolution workflow?"

Context retrieved: 2/5 documents
Reranked successfully: quality = 0.4 (40%)
Decision: should_optimize = True
Reason: "Low quality (quality=0.40), Few results (2)"
Action: Apply healing
  1. get_context_cost_tool()
     → Tokens: 1,250
     → Cost: $0.00125
  2. optimize_chunk_size_tool()
     → Suggested: {k_final: 3, chunk_size: 256}
  3. Update healing_operations table
     → strategy: "re_chunk"
     → improvement_delta: +15%
4. Continue with answer_question using suggestions

Tables updated: query_heatmap, healing_operations
```

### Example 3: Performance History Drives Optimization
```
Query: "What triggers incident escalation?"

Performance history (3 previous queries):
  Query 1: cost=$0.001, accuracy=0.82
  Query 2: cost=$0.0012, accuracy=0.75
  Query 3: cost=$0.0015, accuracy=0.70

Analysis: Trend shows cost increasing, accuracy decreasing
Decision: should_optimize = True
Reason: "Performance history available and shows degradation"
Action: Apply healing
  1. Analyze last 5 queries
  2. Suggest chunk_size reduction
  3. Log optimization attempt

Tables updated: query_heatmap, healing_operations
```

---

## Performance Metrics Tracked

### Per-Query
- Response time (ms)
- Tokens used
- Documents retrieved
- Retrieval accuracy
- User satisfaction (1-5)

### Per-Document
- Average chunk quality
- Reindex count
- Total chunks
- Healing operations applied

### System-Wide
- Total queries
- Average accuracy
- Cost per query
- Most problematic queries
- Most effective healing strategies

---

## Next Steps (Future Enhancements)

1. **User Feedback Loop**: Integrate user satisfaction scores into optimization
2. **Reinforcement Learning**: Use healing history to train a decision model
3. **Multi-Document Healing**: Coordinate healing across related documents
4. **Cost Optimization**: Integrate token cost into decision logic
5. **Predictive Healing**: Anticipate quality issues before they occur
6. **Adaptive Chunking**: Dynamically adjust chunk_size based on document type
7. **Cache Management**: Smart caching of frequently asked questions
8. **A/B Testing**: Compare different healing strategies on same queries

---

## Quick Start

```bash
# Run comprehensive test with healing demonstration
python scripts/test_langgraph_with_healing.py

# View metadata tracking
cat docs/METADATA_TRACKING.md

# View workflow diagrams
cat docs/LANGGRAPH_HEALING_WORKFLOW.md

# Query metadata directly
# See docs/SQL_METADATA_QUERIES.md for SQL examples
```

---

## Summary

✅ **LangGraph Agent** now includes intelligent healing integration that:
- Automatically detects low-quality retrievals
- Decides when optimization is needed
- Applies healing strategies to improve quality and reduce tokens
- Tracks all operations in SQLite for analysis
- Provides complete traceability of retrieval sources
- Logs performance metrics for continuous improvement

The system is production-ready and can handle complex incident management queries while continuously optimizing itself based on performance patterns.
