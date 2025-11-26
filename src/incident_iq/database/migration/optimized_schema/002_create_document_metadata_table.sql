-- Migration: Create Optimized Document Metadata Table
-- Purpose: Consolidate document-level metadata into a single relational table
-- This replaces the old key-value document_metadata table and stores chunking strategy
-- Date: 2025-11-26

CREATE TABLE document_metadata (
    doc_id TEXT PRIMARY KEY,
    
    -- Document Content & Identification
    title TEXT NOT NULL,
    author TEXT,
    source TEXT,
    summary TEXT,
    
    -- Access Control
    rbac_namespace TEXT NOT NULL DEFAULT 'general',
    
    -- Chunking Strategy (document-level defaults)
    chunk_strategy TEXT NOT NULL DEFAULT 'recursive_splitter',
    chunk_size_char INTEGER NOT NULL DEFAULT 512,
    overlap_char INTEGER NOT NULL DEFAULT 50,
    
    -- Consolidated Metadata (sparse/optional fields as JSON)
    -- Stores: categories, keywords, doc_type, created_date, tags, etc.
    metadata_json TEXT,
    
    -- Tracking
    last_ingested TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    CONSTRAINT valid_chunk_size CHECK (chunk_size_char > 0),
    CONSTRAINT valid_overlap CHECK (overlap_char >= 0)
);

-- Create indexes for common queries
CREATE INDEX idx_doc_rbac ON document_metadata(rbac_namespace);
CREATE INDEX idx_doc_created ON document_metadata(last_ingested);
CREATE INDEX idx_doc_author ON document_metadata(author);

-- Example metadata_json structure:
-- {
--   "categories": ["incident_management", "security"],
--   "keywords": ["severity", "priority", "resolution"],
--   "doc_type": "procedure",
--   "created_date": "2025-11-20",
--   "version": "2.1",
--   "tags": ["critical", "approved"]
-- }
