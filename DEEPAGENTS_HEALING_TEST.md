# DeepAgents Healing Agent Test with Metadata Logging

## Overview

This test suite (`test_deepagents_healing.py`) validates the DeepAgents-based RAG system with healing optimization capabilities, ensuring that all operations are logged to the same database tables as the LangGraph implementation for unified metadata tracking.

## Test Coverage

### Test 1: DeepAgents Initialization
- Initializes the `DeepAgentsRAGAgent` with all subagents:
  - **IngestionSubAgent**: Document ingestion, chunking, embedding
  - **RetrievalSubAgent**: Context retrieval and question answering
  - **HealingSubAgent**: System health monitoring and optimization
  - **ConfigSubAgent**: Dynamic configuration adjustments
- Verifies LLM, VectorDB, and Config services are initialized

### Test 2: Document Ingestion with Metadata Logging
- Ingests 3 sample documents via the ingestion subagent
- Logs each ingestion event to `rag_history_and_optimization` table
- Uses `agent_id="deepagents_agent"` for identification
- Fields logged:
  - `query_text`: Document ingestion description
  - `target_doc_id`: Document identifier
  - `metrics_json`: Content length, ingestion status, timestamp
  - `context_json`: Agent type, subagent name, document title

### Test 3: Query Retrieval with Metadata Logging
- Processes 4 test queries through the retrieval subagent
- Logs each query to the metadata table
- Captures answer preview and retrieval status
- Uses same `rag_history_and_optimization` table as LangGraph

### Test 4: Healing Optimization with Metadata Logging
- Executes healing subagent optimization
- Simulates 3 healing actions (OPTIMIZE, RERANK, REINDEX)
- Logs each healing action using `log_healing()` method
- Fields logged:
  - `event_type`: "HEAL"
  - `action_taken`: OPTIMIZE, RERANK, REINDEX
  - `reward_signal`: Quality improvement percentage
  - `metrics_json`: Before/after quality scores
  - `target_doc_id` and `target_chunk_id`: Identifies affected data

### Test 5: Metadata Consistency Verification
- Compares logs from both `deepagents_agent` and `langgraph_agent`
- Verifies all events are in the same unified table
- Counts QUERY and HEAL events by agent type
- Confirms consistency across agent implementations

### Test 6: RL Healing Agent Integration
- Initializes `RLHealingAgent` for intelligent decision-making
- Tests 3 different system states with varying quality/cost metrics
- RL agent decides on actions using epsilon-greedy strategy:
  - **SKIP**: No action needed (high quality)
  - **OPTIMIZE**: Tune parameters
  - **REINDEX**: Refresh embeddings
  - **RE_EMBED**: Change embedding model
- Logs RL decisions to metadata table with agent_id=`deepagents_rl_agent`

## Database Schema

All events are logged to the **`rag_history_and_optimization`** table with these key fields:

```sql
CREATE TABLE rag_history_and_optimization (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,          -- QUERY, HEAL, SYNTHETIC_TEST
    query_text TEXT,                   -- Query or action description
    target_doc_id TEXT,                -- Document being processed
    target_chunk_id TEXT,              -- Specific chunk (for HEAL events)
    metrics_json TEXT,                 -- Performance metrics as JSON
    context_json TEXT,                 -- Additional context as JSON
    action_taken TEXT,                 -- RL action (SKIP, OPTIMIZE, etc.)
    reward_signal REAL,                -- RL reward value
    timestamp TEXT NOT NULL,           -- ISO format timestamp
    agent_id TEXT,                     -- Which agent performed action
    user_id TEXT,                      -- User identifier
    session_id TEXT,                   -- Session identifier
    state_before TEXT,                 -- System state before action
    state_after TEXT                   -- System state after action
);
```

## Running the Test

### Prerequisites
```bash
cd e:\ai-projects\incident_manangement

# Ensure dependencies are installed
pip install -r requirements.txt

# Or install specific packages
pip install deepagents langchain chromadb
```

### Execute the Test
```bash
# From project root
python test_deepagents_healing.py
```

### Expected Output
```
================================================================================
  DeepAgents Healing Agent Test with Metadata Logging
  Unified logging for LangGraph and DeepAgents
================================================================================

Session ID: deepagents_healing_1732700000

[✓] RAGHistoryModel initialized

================================================================================
  TEST 1: DeepAgents RAG Agent Initialization
================================================================================
[✓] DeepAgentsRAGAgent initialized successfully
    - LLM Service: LLMService
    - VectorDB Service: VectorDBService
    - Config Service: ConfigService
    - Ingestion SubAgent: IngestionSubAgent
    - Retrieval SubAgent: RetrievalSubAgent
    - Healing SubAgent: HealingSubAgent
    - Config SubAgent: ConfigSubAgent

[... additional test output ...]

================================================================================
  TEST SUMMARY: DeepAgents Healing with Metadata Logging
================================================================================

[1] INGESTION RESULTS
    Documents processed: 3
    Successfully logged: 3/3

[2] RETRIEVAL RESULTS
    Queries processed: 4
    Successfully logged: 4/4

[3] HEALING RESULTS
    Healing actions processed: 3
    Successfully logged: 3/3

[4] METADATA CONSISTENCY
    Total events logged: 10
    ✓ All agents writing to same table: rag_history_and_optimization

[5] RL INTEGRATION
    RL decisions logged: 3/3

================================================================================
  ✓ DeepAgents Healing Test Complete
  ✓ All metadata logged to rag_history_and_optimization table
  ✓ Consistent with LangGraph agent logging patterns
================================================================================
```

## Comparing with LangGraph

Both implementations log to the same database table, enabling unified analytics:

### LangGraph Logging
- **Agent ID**: `langgraph_agent` or `langgraph_rl_agent`
- **Test File**: `test_e2e_all_components.py`
- **SubAgent equivalent**: LangGraph nodes in workflow graph

### DeepAgents Logging
- **Agent ID**: `deepagents_agent` or `deepagents_rl_agent`
- **Test File**: `test_deepagents_healing.py` (this file)
- **SubAgent equivalent**: DeepAgents SubAgent instances

### Query to Compare Both
```sql
SELECT 
    COUNT(*) as event_count,
    agent_id,
    event_type,
    AVG(CAST(json_extract(reward_signal, '$') AS REAL)) as avg_reward
FROM rag_history_and_optimization
WHERE session_id IN ('langgraph_session_xxx', 'deepagents_healing_xxx')
GROUP BY agent_id, event_type;
```

## Metadata Fields Logged

### For Ingestion (QUERY event type)
```json
{
    "metrics": {
        "doc_id": "doc_001",
        "title": "Document Title",
        "content_length": 1500,
        "ingestion_status": "completed",
        "timestamp": "2025-11-27T..."
    },
    "context": {
        "agent_type": "deepagents",
        "subagent": "IngestionSubAgent",
        "document_title": "Document Title"
    }
}
```

### For Healing (HEAL event type)
```json
{
    "metrics": {
        "action": "OPTIMIZE",
        "target": "chunk_size",
        "quality_before": 0.62,
        "quality_after": 0.78,
        "improvement": 0.16,
        "timestamp": "2025-11-27T..."
    },
    "context": {
        "agent_type": "deepagents",
        "subagent": "HealingSubAgent",
        "reason": "performance_improvement"
    }
}
```

### For RL Decisions (HEAL event type with RL flag)
```json
{
    "metrics": {
        "rl_action": "OPTIMIZE",
        "confidence": 0.85,
        "estimated_improvement": 0.15,
        "estimated_cost": 0.05,
        "state": {
            "quality_score": 0.55,
            "query_accuracy": 0.60,
            "avg_token_cost": 1500
        },
        "timestamp": "2025-11-27T..."
    },
    "context": {
        "agent_type": "deepagents_with_rl",
        "subagent": "HealingSubAgent",
        "rl_decision": "true"
    }
}
```

## Integration Points

### Healing Subagent Tools
1. **check_health()**: Validates embedding quality
2. **estimate_cost()**: Calculates context token costs
3. **optimize_params()**: Adjusts RAG parameters based on history

### RL Agent Integration
- Receives system state (quality, cost, accuracy metrics)
- Decides on action using Q-learning
- Reward signal = Quality_Improvement - Cost_Delta
- Updates action history for future decisions

## Troubleshooting

### ImportError: attempted relative import
**Solution**: Run from project root with `python test_deepagents_healing.py`

### Database Connection Failed
**Solution**: Ensure `chroma_db/rag.db` exists and is initialized:
```bash
python inspect_db_schema.py
```

### DeepAgents SubAgent Not Responding
**Solution**: Check LLM service configuration:
```bash
# Verify LLM config path
echo $env:LLM_CONFIG_PATH
# Should point to src/incident_iq/rag/config/llm_config.json
```

### Missing Dependencies
**Solution**: Install required packages:
```bash
pip install deepagents langchain chromadb sqlite3
```

## Performance Metrics

The test measures:
- **Latency**: Time for each operation
- **Quality Scores**: Before/after healing metrics
- **Token Cost**: LLM token usage
- **Action Effectiveness**: Reward signals from RL agent

## Extensions

To extend this test:

1. **Add Custom Queries**: Modify `TEST_QUERIES` list
2. **Add More Documents**: Expand `SAMPLE_DOCUMENTS` dictionary
3. **Test Specific Healing Actions**: Modify `healing_actions` list
4. **RL Parameter Tuning**: Adjust epsilon/learning_rate in RLHealingAgent
5. **Performance Analysis**: Query metadata table and generate reports

## Related Files

- **DeepAgents Implementation**: `src/incident_iq/rag/agents/deepagents_agent/deepagents_rag_agent.py`
- **RL Healing Agent**: `src/incident_iq/rag/agents/healing_agent/rl_healing_agent.py`
- **Database Model**: `src/incident_iq/database/models/rag_history_model.py`
- **LangGraph Equivalent**: `langgraph_concise_chatbot.py` and `test_e2e_all_components.py`

## Summary

This test validates:
✅ DeepAgents RAG system with all subagents  
✅ Healing optimization with metadata logging  
✅ RL decision-making integration  
✅ Unified metadata table with LangGraph  
✅ Event traceability and consistency  
✅ Query and healing action tracking  

All metadata is logged to the same `rag_history_and_optimization` table, enabling unified analysis across both agent frameworks.
