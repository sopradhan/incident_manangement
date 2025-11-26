# Quick Reference: LangGraph RAG with Intelligent Healing

## 🎯 What You Need to Know

### The System Does 3 Things

1. **Ingests Documents**
   - Extracts metadata (title, author, source, summary)
   - Chunks into manageable pieces
   - Generates embeddings
   - Stores quality scores

2. **Answers Questions**
   - Retrieves relevant chunks
   - Ranks by relevance
   - **Automatically decides**: Should we heal/optimize?
   - Generates answer with full traceability

3. **Optimizes Intelligently**
   - Calculates token cost
   - Suggests parameter changes
   - Tracks improvement
   - Learns from patterns

---

## 📊 SQLite Tables (What Gets Stored)

| Table | What | When |
|-------|------|------|
| `document_metadata` | Titles, authors, summaries | Ingestion |
| `embedding_metadata` | Chunk quality, strategy, size | Ingestion + Optimization |
| `query_heatmap` | Query popularity, accuracy, speed | Every query |
| `healing_operations` | What optimizations were applied | When healing triggered |
| `synthetic_queries` | Auto-generated test questions | Ingestion |

---

## 🧠 Intelligent Healing Decision Tree

```
Query Asked
    ↓
Retrieve Context (5 best chunks)
    ↓
Calculate Quality Score (0-1 scale)
    ↓
Should we optimize?
    ├─ If quality < 0.6 → YES (poor results)
    ├─ If fewer than 3 results → YES (insufficient)
    ├─ If we have performance history → YES (analyze trends)
    └─ Else → NO (skip, just answer)
    ↓
IF YES:
  • Analyze token cost
  • Suggest better parameters
  • Log to healing_operations table
  • Continue to answer
    ↓
ELSE:
  • Skip healing, go straight to answer
    ↓
Generate Answer with Sources
    ↓
Update query_heatmap table
```

---

## 💻 Quick API Usage

```python
from incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent

# Create agent
agent = LangGraphRAGAgent()

# Ingest document
result = agent.ingest_document(
    text="Your document text here...",
    doc_id="doc_001"
)
# Tables updated: document_metadata, embedding_metadata, synthetic_queries

# Ask question
result = agent.ask_question(
    "What are incident severity levels?"
)
# Returns: answer, sources, traceability, optimization_applied, retrieval_quality
# Tables updated: query_heatmap, (optionally) healing_operations

# Response structure:
{
    "answer": "...",
    "sources": [...],
    "traceability": {...},
    "optimization_applied": True/False,
    "optimization_reason": "Quality was 0.4 (low)",
    "retrieval_quality": 0.8,  # 0-1 scale
    "errors": []
}
```

---

## 📈 Key Metrics Tracked

### Per-Query
- ⏱️ Response time (milliseconds)
- 📚 Documents retrieved
- 🎯 Accuracy score (0-100%)
- ⭐ User satisfaction (1-5 stars)
- 💰 Token count and cost

### Per-Document
- 🔤 Number of chunks
- ⭐ Average quality score
- 🔄 Times re-indexed/healed
- 📊 Performance improvements

### System-Wide
- 📊 Total queries processed
- 🎯 Overall accuracy
- 💵 Cost per query
- 🏥 Most effective healing strategies

---

## 🔍 Inspect Your Metadata

### SQL Queries (Copy-Paste Ready)

```sql
-- What metadata was extracted from my document?
SELECT * FROM document_metadata 
WHERE doc_id = 'doc_001'
ORDER BY key;

-- How good are my embeddings?
SELECT 
  chunk_id,
  quality_score,
  healing_suggestions
FROM embedding_metadata
WHERE document_id = 'doc_001'
ORDER BY quality_score ASC;

-- Which queries perform worst?
SELECT 
  query_example,
  frequency,
  ROUND(avg_retrieval_accuracy * 100, 2) as accuracy_pct,
  avg_response_time_ms
FROM query_heatmap
WHERE avg_retrieval_accuracy < 0.7
ORDER BY avg_retrieval_accuracy ASC;

-- What optimizations helped the most?
SELECT 
  strategy,
  AVG(improvement_delta) as avg_improvement_pct,
  COUNT(*) as times_applied
FROM healing_operations
GROUP BY strategy
ORDER BY avg_improvement_pct DESC;
```

---

## 🚀 Three Example Workflows

### Example 1: Perfect Response (No Healing)
```
User: "What are incident severity levels?"

Step 1: retrieve_context → Found 5/5 documents ✓
Step 2: rerank_context → All highly relevant ✓
Step 3: check_optimization → quality=1.0 → NO healing needed
Step 4: answer_question → Generate answer using LLM
Step 5: traceability → Show source attribution

Result: Excellent answer, no optimization needed
Tables updated: query_heatmap (frequency++, accuracy=100%)
```

### Example 2: Poor Response (Healing Applied)
```
User: "What is the incident workflow?"

Step 1: retrieve_context → Found 2/5 documents ✗
Step 2: rerank_context → Low relevance scores
Step 3: check_optimization → quality=0.4 < 0.6 → HEALING NEEDED
Step 4: optimize_context:
  • Calculate tokens: 850 tokens
  • Suggest: reduce chunk_size from 512 → 256
  • Log to healing_operations
Step 5: answer_question → Generate answer
Step 6: traceability → Show sources

Result: Good answer despite initial poor retrieval
Tables updated: query_heatmap, healing_operations
```

### Example 3: Learning from History
```
User: "What triggers escalation?" (3rd similar query)

Performance history shows:
  Query 1: accuracy=82%, cost=$0.001
  Query 2: accuracy=75%, cost=$0.0012
  Query 3: accuracy=70%, cost=$0.0015  ← Getting worse!

Step 1-2: retrieve_context, rerank_context
Step 3: check_optimization → History shows degradation → HEALING NEEDED
Step 4: optimize_context:
  • Analyze trend (accuracy dropping)
  • Suggest parameter adjustment
  • Log improvement suggestions
Step 5-6: answer_question, traceability

Result: System learns and adapts
Tables updated: query_heatmap, healing_operations
```

---

## 📁 File Locations

**Core Code:**
- Agent: `src/incident_iq/rag/agents/langgraph_agent/langgraph_rag_agent.py`
- Tools: `src/incident_iq/rag/tools/`
- Tests: `scripts/test_langgraph_with_healing.py`

**Database:**
- Models: `src/incident_iq/database/models/`
- Database: `./incident_iq.db` (SQLite)

**Documentation:**
- This file: `docs/QUICK_REFERENCE.md`
- Detailed workflows: `docs/LANGGRAPH_HEALING_WORKFLOW.md`
- Metadata guide: `docs/METADATA_TRACKING.md`
- Schema info: `docs/DATABASE_SCHEMA.md`
- SQL queries: `docs/SQL_METADATA_QUERIES.md`
- Full summary: `docs/IMPLEMENTATION_SUMMARY.md`

---

## ⚙️ Configuration

### LLM Provider (ollama by default)
```python
# Location: src/incident_iq/rag/config/llm_config.json
{
  "default_provider": "ollama",
  "llm_providers": {
    "ollama": {
      "base_url": "http://localhost:11434",
      "model": "mistral"
    }
  }
}
```

### Vector Store (ChromaDB)
```python
# Automatic initialization in LangGraphRAGAgent
vectordb_service = VectorDBService(
    persist_directory="./chroma_db",
    collection_name="rag_embeddings"
)
```

---

## 🆘 Troubleshooting

### Problem: "Context retrieval failed: 'StructuredTool' object is not callable"
**Solution:** Tools need `.invoke()` method, not direct call
- ✅ Correct: `retrieve_context_tool.invoke({"param": value})`
- ❌ Wrong: `retrieve_context_tool("param", value=value)`

### Problem: "0 documents retrieved despite successful answer"
**Solution:** Check if sources are being extracted properly
- Verify: `reranked_context.get("reranked_context")` not `.get("ranked_results")`

### Problem: "Healing never triggers"
**Solution:** Check decision logic conditions
```python
# At least ONE of these must be true:
should_optimize = (
    quality < 0.6 or              # Poor quality
    len(reranked) < 3 or          # Too few results
    performance_history exists    # Have history to analyze
)
```

### Problem: "Database connection failed"
**Solution:** Check database path and permissions
- Default location: `./incident_iq.db` in project root
- Ensure write permissions in directory

---

## 📊 Common Queries

```python
# Get document quality stats
from incident_iq.database.models.embedding_model import EmbeddingMetadataModel
emb = EmbeddingMetadataModel()
stats = emb.get_embedding_stats()
print(f"Avg quality: {stats['avg_quality_score']:.2f}")

# Get query performance
from incident_iq.database.models.tracking_model import QueryHeatmapModel
heatmap = QueryHeatmapModel()
analysis = heatmap.get_heatmap_analysis()
print(f"Cold spots: {len(analysis['cold_spots'])}")

# Get healing effectiveness
from incident_iq.database.models.tracking_model import HealingOperationModel
healing = HealingOperationModel()
strategies = healing.get_most_effective_strategies()
for s in strategies:
    print(f"{s['strategy']}: {s['avg_improvement']*100:.1f}% improvement")
```

---

## 🎓 Learning Path

1. **Start Here**: This quick reference
2. **Understand Flow**: `docs/LANGGRAPH_HEALING_WORKFLOW.md`
3. **Deep Dive**: `docs/METADATA_TRACKING.md`
4. **Query Data**: `docs/SQL_METADATA_QUERIES.md`
5. **Schema Details**: `docs/DATABASE_SCHEMA.md`
6. **Full Context**: `docs/IMPLEMENTATION_SUMMARY.md`

---

## ✨ Key Takeaways

✅ **Intelligent**: Automatically decides when to optimize
✅ **Observable**: Every operation tracked in SQLite
✅ **Traceable**: Know exactly which sources were used
✅ **Optimizable**: System learns from performance history
✅ **Scalable**: Works from 1 to millions of documents

---

## 🚦 Next Steps

1. **Ingest** your first document:
   ```python
   agent.ingest_document(your_text, "doc_001")
   ```

2. **Ask** your first question:
   ```python
   result = agent.ask_question("Your question here?")
   ```

3. **Inspect** the results:
   ```python
   print(f"Quality: {result['retrieval_quality']*100:.1f}%")
   print(f"Sources: {len(result['sources'])}")
   print(f"Healing applied: {result['optimization_applied']}")
   ```

4. **Explore** the metadata:
   ```sql
   SELECT * FROM query_heatmap ORDER BY frequency DESC LIMIT 10;
   ```

That's it! The system handles the rest. 🎉

---

## 📞 Support

For detailed information, see:
- **Workflows**: `docs/LANGGRAPH_HEALING_WORKFLOW.md`
- **Metadata**: `docs/METADATA_TRACKING.md`
- **Queries**: `docs/SQL_METADATA_QUERIES.md`
- **Schema**: `docs/DATABASE_SCHEMA.md`
