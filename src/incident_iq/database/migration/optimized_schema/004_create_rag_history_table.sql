-- Migration: Create Optimized RAG History & Optimization Table
-- Purpose: Unified historical log for queries, healing operations, and synthetic tests
-- Consolidates: query_heatmap + healing_operations + synthetic_queries
-- Date: 2025-11-26

CREATE TABLE rag_history_and_optimization (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Event Classification
    event_type TEXT NOT NULL CHECK (event_type IN ('QUERY', 'HEAL', 'SYNTHETIC_TEST')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Query Information (populated if event_type='QUERY' or 'SYNTHETIC_TEST')
    query_text TEXT,
    
    -- Document & Chunk Context (populated if event_type='HEAL' or 'SYNTHETIC_TEST')
    target_doc_id TEXT,
    target_chunk_id TEXT,
    
    -- Performance & Metrics (consolidated as JSON for flexibility)
    -- For QUERY events: {frequency, avg_accuracy, cost, latency, user_feedback}
    -- For HEAL events: {strategy, before_metrics, after_metrics, improvement_delta}
    -- For SYNTHETIC_TEST: {expected_answer, generated_answer, accuracy, latency}
    metrics_json TEXT NOT NULL,
    
    -- Context & Actions (consolidated as JSON for additional details)
    -- Stores: source_attributions, actions_taken, reasoning, suggestions, etc.
    context_json TEXT,
    
    -- RL Agent Tracking (for reinforcement learning)
    reward_signal FLOAT,         -- Reward for this event (0.0-1.0, calculated by RL agent)
    action_taken TEXT,           -- Action chosen by RL agent ("OPTIMIZE", "SKIP", "REINDEX")
    state_before TEXT,           -- System state before action (JSON)
    state_after TEXT,            -- System state after action (JSON)
    
    -- Traceability
    agent_id TEXT DEFAULT 'langgraph_agent',
    user_id TEXT,
    session_id TEXT,
    
    -- Foreign key relationship
    FOREIGN KEY (target_doc_id) REFERENCES document_metadata(doc_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_event_type ON rag_history_and_optimization(event_type);
CREATE INDEX idx_timestamp ON rag_history_and_optimization(timestamp);
CREATE INDEX idx_query_hash ON rag_history_and_optimization(query_text);
CREATE INDEX idx_target_doc ON rag_history_and_optimization(target_doc_id);
CREATE INDEX idx_agent_session ON rag_history_and_optimization(agent_id, session_id);

-- Example QUERY event metrics_json:
-- {
--   "frequency": 3,
--   "avg_accuracy": 0.87,
--   "cost_tokens": 1250,
--   "latency_ms": 342,
--   "user_feedback": 0.9,
--   "quality_category": "warm",
--   "sources_count": 4
-- }

-- Example HEAL event metrics_json:
-- {
--   "strategy": "re_chunk",
--   "before_metrics": {"avg_quality": 0.55, "total_chunks": 12},
--   "after_metrics": {"avg_quality": 0.82, "total_chunks": 18},
--   "improvement_delta": 0.27,
--   "cost_tokens": 500,
--   "duration_ms": 1200
-- }

-- Example SYNTHETIC_TEST event metrics_json:
-- {
--   "expected_answer": "...",
--   "generated_answer": "...",
--   "accuracy": 0.94,
--   "latency_ms": 287,
--   "bleu_score": 0.91
-- }

-- Example RL context_json:
-- {
--   "reason": "low_quality_detected",
--   "threshold_breached": true,
--   "action_rationale": "quality_score=0.45 < threshold=0.6",
--   "alternatives_considered": ["SKIP", "REINDEX", "OPTIMIZE"],
--   "expected_reward": 0.78
-- }
