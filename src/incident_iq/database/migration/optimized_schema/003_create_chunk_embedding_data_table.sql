-- Migration: Create Optimized Chunk Embedding Data Table
-- Purpose: Track per-chunk health, versioning, and quality for RL healing agent
-- One-to-Many relationship with document_metadata via doc_id
-- Date: 2025-11-26

CREATE TABLE chunk_embedding_data (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    
    -- Embedding Information
    embedding_model TEXT NOT NULL,
    embedding_version TEXT,
    
    -- Quality & Health (for Healing/RL Agent)
    quality_score FLOAT DEFAULT 0.8 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    reindex_count INTEGER DEFAULT 0,
    
    -- RL Agent Suggestions & Context
    healing_suggestions TEXT, -- JSON: {"strategy": "re_chunk", "reason": "...", "suggested_params": {...}}
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_healed TIMESTAMP,
    
    -- Foreign key to document_metadata
    FOREIGN KEY (doc_id) REFERENCES document_metadata(doc_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_chunk_doc ON chunk_embedding_data(doc_id);
CREATE INDEX idx_chunk_quality ON chunk_embedding_data(quality_score);
CREATE INDEX idx_chunk_reindex ON chunk_embedding_data(reindex_count);

-- Example healing_suggestions JSON structure:
-- {
--   "strategy": "re_chunk",
--   "reason": "quality_score_below_threshold",
--   "current_params": {"size": 512, "overlap": 50},
--   "suggested_params": {"size": 256, "overlap": 30},
--   "expected_improvement": 0.15,
--   "confidence": 0.92
-- }
