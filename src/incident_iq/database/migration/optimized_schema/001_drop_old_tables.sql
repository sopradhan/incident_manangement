-- Migration: Drop Old Tables
-- Purpose: Remove fragmented metadata schema (5 tables) before creating optimized schema (3 tables)
-- Date: 2025-11-26
-- NOTE: Back up your database before running this!

-- Disable foreign key constraints temporarily
PRAGMA foreign_keys = OFF;

-- Drop old tables in reverse dependency order
-- DROP TABLE IF EXISTS synthetic_queries;
-- DROP TABLE IF EXISTS healing_operations;
-- DROP TABLE IF EXISTS query_heatmap;
-- DROP TABLE IF EXISTS embedding_metadata;
-- DROP TABLE IF EXISTS document_metadata;

-- Re-enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Verification: Check that all old tables are gone
-- SELECT name FROM sqlite_master WHERE type='table' AND name IN ('document_metadata', 'embedding_metadata', 'query_heatmap', 'healing_operations', 'synthetic_queries');
-- This query should return 0 rows if successful.
