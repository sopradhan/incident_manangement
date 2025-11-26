# Complete Response Mode Workflows

## Overview
Three user types, three workflows, all backed by LangGraph RAG Agent

---

## Workflow 1: CONCISE Mode - Interactive Chatbot

**User Type**: End-users, customers

**Flow**:
```
┌─────────────────────────────────────────────────────────┐
│  INTERACTIVE CONCISE MODE - INCIDENT MANAGEMENT Q&A     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  1. Ask a question (or 'quit' to exit):                 │
│     > What is incident management?                      │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │  LangGraph Agent Backend:           │
        │  - Retrieve context                 │
        │  - Rerank documents                 │
        │  - Generate answer                  │
        │  - Log to database                  │
        │  - Generate visualizations          │
        └─────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. Answer (Plain Text):                                │
│     "Incident management is the process of identifying, │
│      reporting, triaging, assigning, investigating,     │
│      implementing fixes or workarounds, testing and     │
│      verifying, documenting, closing, and conducting    │
│      post-investigation reviews for incidents."         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. Are you satisfied with this answer?                 │
│     > (yes/no)                                          │
└─────────────────────────────────────────────────────────┘
                ↙                            ↘
           (yes)                           (no)
             ↓                              ↓
      ┌────────────────┐        ┌──────────────────────┐
      │ Move to next   │        │ Re-run LangGraph     │
      │ question       │        │ for same question    │
      └────────────────┘        └──────────────────────┘
             ↓                              ↓
      ┌────────────────┐        ┌──────────────────────┐
      │ Ask question   │        │ Show new answer      │
      │ again          │        │ Ask satisfaction     │
      └────────────────┘        └──────────────────────┘
             ↓
       (repeat until quit)
             ↓
      ┌────────────────┐
      │ Workflow ends  │
      └────────────────┘
```

**Response Format**:
```json
{
  "success": true,
  "question": "What is incident management?",
  "answer": "Incident management is the process...",
  "session_id": "uuid...",
  "errors": []
}
```

**Test Command**:
```bash
python test_concise_interactive.py
```

**Example Session**:
```
Question: What is incident management?
Answer: Incident management is the process of identifying...
Are you satisfied? (yes/no): no

[?] Let me try again to find better information...

Question: What is incident management?
Answer: Incident management involves identifying, reporting...
Are you satisfied? (yes/no): yes

[OK] Great! Moving on...

Ask a question (or 'quit' to exit): quit
[OK] Workflow ended. Thank you!
```

---

## Workflow 2: VERBOSE Mode - Admin Diagnostics

**User Type**: Engineers, RAG Administrators

**Flow**:
```
┌─────────────────────────────────────────────────────────┐
│  VERBOSE MODE - ADMIN DASHBOARD                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Query: "What is incident management?"                  │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │  LangGraph Agent Backend:           │
        │  - Retrieve context                 │
        │  - Rerank documents                 │
        │  - Generate answer                  │
        │  - Apply RL optimization (if needed)│
        │  - Log to database                  │
        │  - Generate visualizations          │
        │  - Debug output enabled             │
        └─────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Response (FULL METADATA):                              │
│  {                                                      │
│    "success": true,                                     │
│    "answer": "Incident management is...",              │
│    "retrieval_quality": 1.00,                           │
│    "sources_count": 5,                                  │
│    "rl_action": "SKIP",                                 │
│    "optimization_applied": false,                       │
│    "execution_time_ms": 10079,                          │
│    "traceability": {...},                               │
│    "visualization_data": {...},                         │
│    "rl_recommendation": {...}                           │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ADMIN ANALYSIS:                                        │
│  - Quality score: 1.00 ✓                                │
│  - 5 documents retrieved ✓                              │
│  - No RL optimization needed                            │
│  - Execution time: 10 seconds                           │
│  - Full traceability for audit trail                    │
│  - Visualization PNG generated                          │
└─────────────────────────────────────────────────────────┘
```

**Use Case**:
- Debug RAG behavior
- Check retrieval quality
- Monitor RL optimization triggers
- Review traceability
- Analyze performance

**Response Fields**:
- answer, question, session_id
- retrieval_quality, sources_count
- rl_action, rl_recommendation
- optimization_applied, optimization_reason
- execution_time_ms
- traceability, visualization_data
- errors

**Test Command**:
```bash
python test_agent_all_modes.py  # Includes verbose mode
```

---

## Workflow 3: INTERNAL Mode - System Integration

**User Type**: Backend systems, databases, automation

**Flow**:
```
┌─────────────────────────────────────────────────────────┐
│  INTERNAL MODE - DATABASE UPDATE PIPELINE               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Query from System: "What is incident management?"      │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │  LangGraph Agent Backend:           │
        │  - Retrieve context                 │
        │  - Rerank documents                 │
        │  - Generate answer                  │
        │  - Log to database                  │
        │  - (No user approval needed)        │
        └─────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Response (STRUCTURED DATA):                            │
│  {                                                      │
│    "success": true,                                     │
│    "answer": "Incident management is the process...",  │
│    "quality_score": 1.00,                               │
│    "sources_count": 5,                                  │
│    "source_docs": [                                     │
│      {"doc_id": "doc_incident_001",                     │
│       "chunk_id": "chunk_123"},                         │
│      ...                                                │
│    ],                                                   │
│    "metadata": {                                        │
│      "session_id": "uuid...",                           │
│      "timestamp": 1732614624.123,                       │
│      "model": "langgraph_rag_agent",                    │
│      "execution_time_ms": 7642                          │
│    }                                                    │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │  AUTO-UPDATE DATABASE:              │
        │  - Insert into qa_answers table     │
        │  - Link to source documents         │
        │  - Record quality score             │
        │  - Timestamp the response           │
        │  - Update related tables            │
        └─────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Database State Updated ✓                               │
│  No user interaction needed                             │
│  Ready for next question                                │
└─────────────────────────────────────────────────────────┘
```

**Use Case**:
- Automated QA pipeline
- Database population
- System integration
- Batch processing
- No user approval needed

**Response Fields**:
- answer (plain text)
- success, quality_score
- sources_count, source_docs
- metadata (session_id, timestamp, execution_time_ms)
- errors

**Test Command**:
```bash
python test_internal_mode.py
```

---

## Comparison Table

| Aspect | Concise | Verbose | Internal |
|--------|---------|---------|----------|
| **User Type** | End-users | Engineers | Systems |
| **Answer Format** | Plain text | Full metadata | Plain text + structured |
| **Interaction** | Interactive loop | One-time query | Automatic |
| **Approval Flow** | User satisfaction | N/A | Auto-execute |
| **Debug Output** | None | Full | None |
| **Use Case** | Chat interface | Diagnostics | Database updates |
| **Response Time** | ~8-16s | ~10-14s | ~7-9s |
| **Session Handling** | Chat history | Single query | Pipeline |

---

## Key Features Across All Modes

### Shared Features
✓ **LangGraph Backend**: All modes use same RAG agent
✓ **Database Logging**: Query logged to `rag_history_and_optimization` table
✓ **Session Tracking**: Every response has `session_id`
✓ **Error Handling**: All modes return errors if query fails
✓ **Chat History**: Saved to `data/chat_history/` for all modes
✓ **Execution Traces**: PNG visualizations generated for all modes
✓ **Quality Metrics**: All modes capture retrieval quality

### Mode-Specific Features

**Concise**:
- Interactive prompt loop
- User satisfaction feedback
- Loop on "no" to re-run LangGraph
- Clean UX (answer only)

**Verbose**:
- Full debugging information
- RL agent recommendations
- Traceability details
- Optimization analysis

**Internal**:
- Structured source metadata
- Auto-ready for database insert
- Timestamp included
- Model metadata for audit

---

## Testing All Workflows

```bash
# 1. Interactive Concise (Chatbot)
python test_concise_interactive.py

# 2. All Modes (3 questions × 3 modes)
python test_agent_all_modes.py

# 3. Internal Mode Only
python test_internal_mode.py

# 4. Original 5-Question Test
python test_agent_5_questions.py
```

---

## Session Persistence

All modes support session resumption:

```python
# Session data saved to:
data/chat_history/session_YYYYMMDD_HHMMSS.json

# Contains:
{
  "concise": [...],      # All concise mode queries
  "verbose": [...],      # All verbose mode queries
  "internal": [...]      # All internal mode queries
}
```

Each entry includes:
- timestamp
- question
- response
- elapsed_ms

Resume a session by loading the JSON and replaying questions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 USER INTERFACE LAYER                     │
│  Concise     │     Verbose      │      Internal          │
│  (Chatbot)   │  (Admin Board)   │   (Pipeline)           │
└────────────┬───────────┬─────────────────┬───────────────┘
             │           │                 │
             └───────────┴────────┬────────┘
                                  │
┌─────────────────────────────────▼─────────────────────────┐
│          LangGraph RAG Agent (Backend)                     │
│  - retrieve_context_node                                 │
│  - rerank_context_node                                   │
│  - check_optimization_needed                             │
│  - optimize_context_node                                 │
│  - answer_question_node                                  │
│  - traceability_node                                     │
└──┬──────────────┬──────────────┬──────────────┬───────────┘
   │              │              │              │
   ▼              ▼              ▼              ▼
[VectorDB]   [LLM Service]  [RL Healing]  [Database]
[ChromaDB]   [Ollama/LLM]   [Agent]       [rag.db]
```

---

## Production Deployment

For production use:
1. Start with **Concise** for user-facing features
2. Add **Verbose** for admin dashboards
3. Add **Internal** for backend automation

Each mode can be deployed independently or together.

