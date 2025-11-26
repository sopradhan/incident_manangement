# Response Modes Documentation

## Overview
LangGraph RAG Agent now supports three response modes designed for different user types:

---

## 1. CONCISE Mode (End-User Friendly)
**Target Users**: End-users, customers, general audience

**Response Fields**:
- `success`: Boolean status
- `question`: The question asked
- `answer`: Plain text answer
- `session_id`: Session identifier for tracking
- `errors`: Any errors that occurred

**Use Case**: Best for chat interfaces, customer support portals, or any UX where users just want the answer without technical details.

**Example**:
```python
response = agent.ask_question(
    question="What is incident management?",
    response_mode="concise"
)

# Output:
# {
#   "success": true,
#   "question": "What is incident management?",
#   "answer": "Incident management is the process of...",
#   "session_id": "d4daad6d-...",
#   "errors": []
# }
```

---

## 2. VERBOSE Mode (Engineer/RAG Admin)
**Target Users**: Engineers, RAG administrators, system engineers

**Response Fields**:
- All concise fields PLUS:
- `sources`: Full source documents retrieved
- `sources_count`: Number of source documents
- `traceability`: Complete traceability information
- `retrieval_quality`: Quality score (0.0-1.0)
- `optimization_applied`: Whether RL optimization was triggered
- `optimization_reason`: Why optimization was applied
- `rl_action`: RL agent action (SKIP, OPTIMIZE, HEAL, etc.)
- `rl_recommendation`: Detailed RL recommendations with confidence
- `optimization_result`: Results of any optimizations
- `execution_time_ms`: Total execution time
- `visualization_data`: Full execution trace data

**Use Case**: For debugging, performance analysis, quality assurance, and understanding RAG behavior.

**Example**:
```python
response = agent.ask_question(
    question="What is incident management?",
    response_mode="verbose"
)

# Output includes:
# {
#   "success": true,
#   "retrieval_quality": 1.00,
#   "sources_count": 5,
#   "rl_action": "SKIP",
#   "optimization_applied": false,
#   "execution_time_ms": 10079,
#   "traceability": { ... },
#   "visualization_data": { ... },
#   ...
# }
```

---

## 3. INTERNAL Mode (System/Integration)
**Target Users**: Backend systems, data integration pipelines, admin dashboards

**Response Fields**:
- `success`: Boolean status
- `question`: The question asked
- `answer`: Plain text answer
- `session_id`: Session identifier
- `sources`: Full source documents
- `sources_count`: Number of sources
- `quality_score`: Retrieval quality
- `source_docs`: Structured source info (doc_id, chunk_id) for database updates
- `metadata`: Structured metadata with timestamp, model, execution time
- `traceability`: Traceability information
- `errors`: Any errors

**Use Case**: For system-to-system integration, updating other tables/databases with structured data from RAG responses.

**Example**:
```python
response = agent.ask_question(
    question="What is incident management?",
    response_mode="internal"
)

# Output includes:
# {
#   "success": true,
#   "answer": "Incident management is...",
#   "quality_score": 1.00,
#   "source_docs": [
#     {"doc_id": "doc_incident_001", "chunk_id": "chunk_123"},
#     ...
#   ],
#   "metadata": {
#     "timestamp": 1732614624.123,
#     "model": "langgraph_rag_agent",
#     "execution_time_ms": 7642
#   },
#   ...
# }
```

---

## Usage Examples

### Example 1: End-User Chat Interface
```python
from src.incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# User asks question via chat
response = agent.ask_question(
    question="How do we handle critical incidents?",
    response_mode="concise"
)

# Display just the answer
print(response["answer"])
# Output: "To handle a critical incident, follow these steps: 1. Detect the issue... 2. Log..."
```

### Example 2: Admin Debugging Dashboard
```python
# Admin wants full diagnostic information
response = agent.ask_question(
    question="How do we handle critical incidents?",
    response_mode="verbose"
)

# Display quality metrics
print(f"Retrieval Quality: {response['retrieval_quality']:.2f}")
print(f"Sources Found: {response['sources_count']}")
print(f"Execution Time: {response['execution_time_ms']:.0f}ms")
print(f"RL Optimization: {response['optimization_applied']}")

# Access trace data for visualization
viz_data = response["visualization_data"]
```

### Example 3: Database Integration
```python
# System wants to update related tables with structured data
response = agent.ask_question(
    question="How do we handle critical incidents?",
    response_mode="internal"
)

# Extract structured source information
for source in response["source_docs"]:
    doc_id = source["doc_id"]
    chunk_id = source["chunk_id"]
    # Update related_incidents table
    db.insert_incident_reference(doc_id, chunk_id, response["answer"])

# Extract metadata for audit trail
audit_entry = {
    "question": response["question"],
    "answer_quality": response["quality_score"],
    "sources_used": response["sources_count"],
    "timestamp": response["metadata"]["timestamp"],
    "model": response["metadata"]["model"]
}
db.log_audit_trail(audit_entry)
```

---

## Chat History & Session Persistence

All responses include a `session_id` which can be used for:
- Tracking conversation history
- Resuming sessions
- Caching with tiktoken
- Analytics and audit trails

Chat history is automatically persisted to:
```
data/chat_history/session_YYYYMMDD_HHMMSS.json
```

Example structure:
```json
{
  "concise": [
    {
      "timestamp": "2025-11-27T00:39:24...",
      "question": "What is incident management?",
      "response": { ... },
      "elapsed_ms": 7697
    }
  ],
  "verbose": [ ... ],
  "internal": [ ... ]
}
```

---

## Summary Table

| Feature | Concise | Verbose | Internal |
|---------|---------|---------|----------|
| **User Type** | End-users | Engineers/Admins | Backend Systems |
| **Answer** | ✓ | ✓ | ✓ |
| **Sources** | ✗ | ✓ | ✓ |
| **Quality Score** | ✗ | ✓ | ✓ |
| **Traceability** | ✗ | ✓ | ✓ |
| **RL Info** | ✗ | ✓ | ✗ |
| **Visualization** | ✗ | ✓ | ✗ |
| **Structured Data** | ✗ | ✗ | ✓ |
| **Metadata** | ✗ | ✗ | ✓ |

---

## Default Behavior

- Default response_mode: `"concise"`
- All modes save execution traces to `logs/` and `session_graph/`
- Debug output is only shown in `verbose` mode
- PNG visualizations are generated for all modes but only logged in verbose mode

---

## Testing

Run comprehensive test with all modes:
```bash
python test_agent_all_modes.py
```

This will:
1. Test 3 questions across all 3 modes
2. Display mode-specific output
3. Show chat history summary
4. Save persistent session data
