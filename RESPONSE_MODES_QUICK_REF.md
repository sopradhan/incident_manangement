# Quick Reference - Response Modes

## Three User Types, Three Modes

### 1️ CONCISE Mode - End Users
```python
response = agent.ask_question(question="...", response_mode="concise")

# Output:
{
    "success": true,
    "question": "What is incident management?",
    "answer": "Incident management is the process of...",
    "session_id": "uuid...",
    "errors": []
}
```
**Best for**: Chat interfaces, customer portals, end-user UX
**Answer**: Just the answer text

---

### 2️ VERBOSE Mode - Engineers/Admins
```python
response = agent.ask_question(question="...", response_mode="verbose")

# Output:
{
    "success": true,
    "question": "...",
    "answer": "...",
    "retrieval_quality": 1.00,
    "sources_count": 5,
    "rl_action": "SKIP",
    "optimization_applied": false,
    "execution_time_ms": 10079,
    "traceability": {...},
    "visualization_data": {...},
    "rl_recommendation": {...},
    ...
}
```
**Best for**: Debugging, performance analysis, RAG diagnostics
**Answer**: Full metadata, traceability, RL info, execution traces

---

### 3️ INTERNAL Mode - Backend Systems
```python
response = agent.ask_question(question="...", response_mode="internal")

# Output:
{
    "success": true,
    "answer": "Incident management is the process of identifying, reporting, triaging...",
    "quality_score": 1.00,
    "sources_count": 5,
    "source_docs": [
        {"doc_id": "doc_incident_001", "chunk_id": "chunk_123"},
        ...
    ],
    "metadata": {
        "session_id": "uuid...",
        "timestamp": 1732614624.123,
        "model": "langgraph_rag_agent",
        "execution_time_ms": 16485
    },
    "errors": []
}
```
**Best for**: Database updates, system integration, automated pipelines
**Answer**: Plain text (no JSON wrapping), structured source metadata

---

## Response Field Comparison

| Field | Concise | Verbose | Internal |
|-------|---------|---------|----------|
| answer | ✓ | ✓ | ✓ (plain text) |
| question | ✓ | ✓ | ✗ |
| session_id | ✓ | ✓ | metadata.session_id |
| success | ✓ | ✓ | ✓ |
| errors | ✓ | ✓ | ✓ |
| sources | ✗ | ✓ | ✓ (source_docs) |
| quality_score | ✗ | retrieval_quality | ✓ |
| traceability | ✗ | ✓ | ✗ |
| rl_info | ✗ | ✓ | ✗ |
| visualization_data | ✗ | ✓ | ✗ |
| execution_time | ✗ | ✓ | metadata |

---

## Usage Patterns

### Pattern 1: End-User Chat
```python
response = agent.ask_question(question, response_mode="concise")
print(f"Q: {response['question']}")
print(f"A: {response['answer']}")
# No approval prompt, just display
```

### Pattern 2: Admin Dashboard
```python
response = agent.ask_question(question, response_mode="verbose")
dashboard.display_metrics({
    "quality": response['retrieval_quality'],
    "sources": response['sources_count'],
    "rl_action": response['rl_action'],
    "time_ms": response['execution_time_ms']
})
```

### Pattern 3: Database Integration
```python
response = agent.ask_question(question, response_mode="internal")

# Auto-update table (no approval needed)
for source in response['source_docs']:
    db.insert_qa_log({
        "question": question,
        "answer": response['answer'],  # Plain text
        "quality": response['quality_score'],
        "doc_id": source['doc_id'],
        "timestamp": response['metadata']['timestamp']
    })
```

---

## Key Differences

### Answer Format
- **Concise & Verbose**: May contain JSON structure
- **Internal**: Plain text only (JSON stripped if present)

### Metadata
- **Concise**: Minimal (session_id only)
- **Verbose**: Full (traceability, visualization, RL info)
- **Internal**: Structured (`metadata` dict with timestamp, model, execution_time)

### Use Case
- **Concise**: "Show user the answer"
- **Verbose**: "Help engineer debug the system"
- **Internal**: "Feed data to another system"

### Approval Flow
- **Concise**: Display, no approval needed
- **Verbose**: Admin reviews then acts
- **Internal**: Automatic (no user interaction)

---

## Default Behavior
- Default mode: `"concise"`
- All modes log to database and generate traces
- All modes have `session_id` for tracking
- Chat history auto-saved to `data/chat_history/`

---

## Testing
```bash
# Test all modes
python test_agent_all_modes.py

# Test internal mode only
python test_internal_mode.py
```
