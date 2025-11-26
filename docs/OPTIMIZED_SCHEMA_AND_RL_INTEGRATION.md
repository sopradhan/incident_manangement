# Complete RAG System: Optimized Schema + RL Healing Integration

## Overview

This document describes the complete solution combining:
1. **Optimized 3-Table SQLite Schema** (reduced from 5 tables)
2. **Reinforcement Learning (RL) Healing Agent** (intelligent optimization)
3. **LangGraph Integration** (intelligent decision-making during retrieval)

---

## Architecture: 3-Table Optimized Schema

### Table 1: `document_metadata`
**Primary source of truth for documents and their chunking strategy**

```
doc_id (PK)
├─ title, author, source, summary
├─ rbac_namespace (access control)
├─ chunk_strategy, chunk_size_char, overlap_char (chunking params)
├─ metadata_json (categories, keywords, doc_type, version, tags)
└─ last_ingested (tracking)
```

**Purpose:** Single document-level record with all chunking strategy info

---

### Table 2: `chunk_embedding_data`
**One-to-Many relationship with documents**

```
chunk_id (PK)
├─ doc_id (FK → document_metadata.doc_id)
├─ embedding_model, embedding_version
├─ quality_score (0.0-1.0) ← Updated by RL Healing Agent
├─ reindex_count ← Tracks healing history
├─ healing_suggestions (JSON with RL recommendations)
└─ created_at, last_healed
```

**Purpose:** Track individual chunk health and RL agent's healing suggestions

---

### Table 3: `rag_history_and_optimization`
**Unified event log: queries, healing operations, synthetic tests**

```
history_id (PK, auto-increment)
├─ event_type: 'QUERY' | 'HEAL' | 'SYNTHETIC_TEST'
├─ timestamp
├─ query_text (for QUERY/SYNTHETIC_TEST events)
├─ target_doc_id, target_chunk_id (FK → document_metadata)
├─ metrics_json (flexible structure per event type)
├─ context_json (details, reasoning, source attributions)
├─ reward_signal (0.0-1.0) ← RL reward
├─ action_taken (RL action: SKIP, OPTIMIZE, REINDEX, RE_EMBED)
├─ state_before, state_after (JSON for RL state transition)
└─ agent_id, user_id, session_id (traceability)
```

**Purpose:** Complete historical log with RL decision tracking

---

## Relationships & Joins

### Join 1: Complete Document Picture
```sql
SELECT d.doc_id, d.title, d.chunk_size_char,
       COUNT(c.chunk_id) as chunks,
       AVG(c.quality_score) as avg_quality,
       SUM(c.reindex_count) as total_heals
FROM document_metadata d
LEFT JOIN chunk_embedding_data c ON d.doc_id = c.doc_id
GROUP BY d.doc_id;
```

### Join 2: Healing History
```sql
SELECT d.doc_id, d.title,
       json_extract(h.metrics_json, '$.strategy') as strategy,
       COUNT(*) as times_healed,
       AVG(CAST(json_extract(h.metrics_json, '$.improvement_delta') AS FLOAT))
FROM rag_history_and_optimization h
JOIN document_metadata d ON h.target_doc_id = d.doc_id
WHERE h.event_type = 'HEAL'
GROUP BY d.doc_id, strategy;
```

### Join 3: Query Performance Heatmap
```sql
SELECT h.query_text,
       COUNT(*) as frequency,
       AVG(CAST(json_extract(h.metrics_json, '$.avg_accuracy') AS FLOAT)) as accuracy,
       d.title
FROM rag_history_and_optimization h
LEFT JOIN document_metadata d ON h.target_doc_id = d.doc_id
WHERE h.event_type = 'QUERY'
GROUP BY h.query_text;
```

---

## RL Healing Agent: Reinforcement Learning

### State Variables

```python
state = {
    "quality_score": 0.55,        # Current chunk quality (0-1)
    "query_accuracy": 0.82,       # Retrieval accuracy
    "chunk_count": 24,            # Total chunks in document
    "avg_token_cost": 1200,       # Average tokens per query
    "reindex_count": 1,           # Times reindexed
    "query_frequency": 42,        # How often queried
    "user_feedback": 0.78         # Average user satisfaction
}
```

### Actions

| Action | Use Case | Cost | Expected Gain |
|--------|----------|------|---------------|
| **SKIP** | Quality > 0.75 | 0 | 0% |
| **OPTIMIZE** | Quality 0.5-0.75, tune chunk size | 500 tokens | 8-15% |
| **REINDEX** | Re-embed with same params | 300 tokens | 5-12% |
| **RE_EMBED** | Switch embedding model | 800 tokens | 15-25% |

### Reward Function

```python
reward = (quality_improvement - normalized_cost) * confidence
        = (delta_quality - cost/1000) * confidence
```

Example:
- Action improved quality: 0.55 → 0.70 (delta = 0.15)
- Cost: 500 tokens (normalized = 0.5)
- Confidence: 0.85
- Reward = (0.15 - 0.5) * 0.85 = -0.30 (net negative, not recommended)

### Learning: Epsilon-Greedy

```
Initial: epsilon = 0.30 (30% exploration)
After each action: epsilon *= 0.995 (decay towards exploitation)
Minimum: epsilon = 0.05 (always explore 5%)
```

The agent learns which actions work best:
- **Q-values**: Track average reward per (state, action) pair
- **Action History**: `{'SKIP': {count, total_reward, avg_reward}, ...}`
- **Decision**: Choose action with highest Q-value (exploit) or random (explore)

---

## Integration in LangGraph

### Retrieval Workflow with Intelligent Healing

```
START
  ↓
retrieve_context (5 semantic searches)
  ↓
rerank_context (by relevance)
  ↓
check_optimization_needed ← RL Agent decides here
  │
  ├─ YES: optimize_context → analyze costs, suggest params
  │                           ↓
  └─ NO:  skip directly ──→ answer_question
                           ↓
                    traceability_tool
                           ↓
                          END
```

### RL Decision Point

```python
# In check_optimization_needed node:
recommendation = rl_healing_agent.recommend_healing(
    doc_id="doc_001",
    current_quality=0.55  # Low quality triggers analysis
)

# Returns:
{
    "recommended_action": "OPTIMIZE",
    "parameters": {
        "new_chunk_size": 256,
        "new_overlap": 26,
        "strategy": "recursive_splitter"
    },
    "expected_improvement": 0.15,
    "estimated_cost": 500,
    "confidence": 0.82,
    "reasoning": "Quality is below target. Optimizing chunk parameters..."
}
```

### Response to User

```python
result = agent.ask_question(
    question="What are incident severity levels?",
    doc_id="doc_001"
)

{
    "answer": "...",
    "sources_count": 4,
    "retrieval_quality": 0.80,
    
    # RL Info
    "rl_action": "OPTIMIZE",
    "rl_recommendation": {
        "action": "OPTIMIZE",
        "confidence": 0.82,
        "expected_improvement": 0.15,
        "learning_stats": {
            "total_decisions": 127,
            "epsilon": 0.18,
            "best_action": "OPTIMIZE",
            "actions": {
                "SKIP": {"count": 45, "avg_reward": 0.05},
                "OPTIMIZE": {"count": 52, "avg_reward": 0.12},
                "REINDEX": {"count": 20, "avg_reward": 0.08},
                "RE_EMBED": {"count": 10, "avg_reward": 0.14}
            }
        }
    },
    "optimization_applied": True,
    "optimization_reason": "Quality 0.55 < threshold 0.60"
}
```

---

## Migration Process

### Step 1: Backup Old Database
```bash
cp rag.db rag.db.backup
```

### Step 2: Run Migration
```bash
python src/incident_iq/database/migration/optimized_schema/run_migration.py
```

This will:
1. ✅ Drop old tables (document_metadata, embedding_metadata, query_heatmap, healing_operations, synthetic_queries)
2. ✅ Create new optimized tables (document_metadata, chunk_embedding_data, rag_history_and_optimization)
3. ✅ Verify schema correctness
4. ✅ Display relationship diagrams

### Step 3: Reingest Documents
```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()
result = agent.ingest_document(
    text="Document content...",
    doc_id="doc_001"
)
```

---

## SQL Examples: Complete Picture

### Query 1: Document Health Dashboard
```sql
SELECT 
    d.doc_id,
    d.title,
    COUNT(DISTINCT c.chunk_id) as total_chunks,
    AVG(c.quality_score) as avg_quality,
    COUNT(DISTINCT CASE WHEN h.event_type='QUERY' THEN h.history_id END) as total_queries,
    COUNT(DISTINCT CASE WHEN h.event_type='HEAL' THEN h.history_id END) as healing_count,
    SUM(CASE WHEN h.event_type='HEAL' THEN CAST(json_extract(h.metrics_json, '$.improvement_delta') AS FLOAT) ELSE 0 END) as total_improvement
FROM document_metadata d
LEFT JOIN chunk_embedding_data c ON d.doc_id = c.doc_id
LEFT JOIN rag_history_and_optimization h ON h.target_doc_id = d.doc_id
GROUP BY d.doc_id;
```

### Query 2: RL Agent Learning Progress
```sql
SELECT 
    strftime('%Y-%m-%d', h.timestamp) as date,
    json_extract(h.action_taken, '$') as action,
    COUNT(*) as decisions,
    AVG(h.reward_signal) as avg_reward,
    MAX(h.reward_signal) as best_reward
FROM rag_history_and_optimization h
WHERE h.action_taken IS NOT NULL
GROUP BY date, action
ORDER BY date DESC;
```

### Query 3: Most Effective Healing Strategies
```sql
SELECT 
    json_extract(h.metrics_json, '$.strategy') as strategy,
    COUNT(*) as times_used,
    AVG(CAST(json_extract(h.metrics_json, '$.improvement_delta') AS FLOAT)) as avg_improvement,
    SUM(CAST(json_extract(h.metrics_json, '$.cost_tokens') AS FLOAT)) as total_cost,
    (
        AVG(CAST(json_extract(h.metrics_json, '$.improvement_delta') AS FLOAT)) / 
        NULLIF(SUM(CAST(json_extract(h.metrics_json, '$.cost_tokens') AS FLOAT)), 0)
    ) as roi
FROM rag_history_and_optimization h
WHERE h.event_type = 'HEAL'
GROUP BY strategy
ORDER BY roi DESC;
```

---

## Benefits of This Architecture

### Schema Optimization
- ✅ **Table Reduction**: 5 tables → 3 tables (40% reduction)
- ✅ **Flexibility**: JSON fields allow evolution without schema changes
- ✅ **Relationships**: Clear parent-child relationships with foreign keys
- ✅ **Scalability**: Efficient querying with proper indexing

### RL Healing Integration
- ✅ **Intelligent Decisions**: Not just threshold-based, learns from history
- ✅ **Cost-Aware**: Balances improvement vs resource usage
- ✅ **Exploration**: Tries new strategies while exploiting known good ones
- ✅ **Trackable**: Every decision logged with reward and state transition

### LangGraph Integration
- ✅ **Conditional Routing**: Only optimize when RL recommends it
- ✅ **Full Visibility**: Users see RL reasoning in responses
- ✅ **Performance**: Quick skip when no optimization needed
- ✅ **Learning**: Continuous improvement as RL refines decisions

---

## Configuration & Tuning

### RL Agent Parameters
```python
agent = RLHealingAgent(
    db_path="./chroma_db/rag.db",
    initial_epsilon=0.3          # Start with 30% exploration
)

# Tunable in code:
agent.learning_rate = 0.1        # How fast to update Q-values
agent.discount_factor = 0.9      # Future reward weight
agent.epsilon = 0.05             # Minimum exploration (after decay)
```

### Document Chunking
```python
# Set in document_metadata table
chunk_strategy = "recursive_splitter"  # or other strategies
chunk_size_char = 512                  # characters per chunk
overlap_char = 50                      # overlap between chunks
```

### Query Retrieval
```python
# Set in retrieval workflows
k = 5              # Number of top chunks to retrieve
rbac_namespace = "general"  # Access control namespace
```

---

## Monitoring & Analysis

### Check RL Agent Performance
```python
stats = agent.get_learning_stats()
print(f"Best action: {stats['best_action']}")
print(f"Epsilon (exploration rate): {stats['epsilon']:.2%}")
for action, data in stats['actions'].items():
    print(f"{action}: {data['percentage']:.1f}% usage, {data['avg_reward']:.4f} avg reward")
```

### Query Performance Trends
```sql
-- How is the system improving over time?
SELECT 
    DATE(h.timestamp) as day,
    AVG(CAST(json_extract(h.metrics_json, '$.avg_accuracy') AS FLOAT)) as accuracy,
    AVG(CAST(json_extract(h.metrics_json, '$.user_feedback') AS FLOAT)) as satisfaction
FROM rag_history_and_optimization h
WHERE h.event_type = 'QUERY'
GROUP BY day
ORDER BY day;
```

---

## Files Organization

```
src/incident_iq/
├── database/
│   └── migration/
│       └── optimized_schema/
│           ├── 001_drop_old_tables.sql
│           ├── 002_create_document_metadata_table.sql
│           ├── 003_create_chunk_embedding_data_table.sql
│           ├── 004_create_rag_history_table.sql
│           ├── advanced_queries.sql
│           └── run_migration.py
│
└── rag/
    └── agents/
        ├── healing_agent/
        │   ├── __init__.py
        │   └── rl_healing_agent.py
        └── langgraph_agent/
            └── langgraph_rag_agent.py (integrated with RL)
```

---

## Next Steps

1. **Run Migration**: Execute `run_migration.py` to create new schema
2. **Test Ingestion**: Ingest documents with new schema
3. **Monitor RL**: Check agent learning stats after queries
4. **Tune Parameters**: Adjust epsilon, chunk sizes based on performance
5. **Analyze Trends**: Use SQL queries to find best healing strategies

