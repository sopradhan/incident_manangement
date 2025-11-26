-- Advanced Queries: Complete Picture via Table Joins
-- Purpose: Show how to combine all three tables for comprehensive analysis
-- Date: 2025-11-26

-- ========================================
-- Query 1: Complete Document & Chunk Overview
-- Purpose: See all chunks for a document with their quality scores
-- ========================================
SELECT 
    d.doc_id,
    d.title,
    d.author,
    d.chunk_size_char,
    d.overlap_char,
    COUNT(c.chunk_id) as total_chunks,
    AVG(c.quality_score) as avg_chunk_quality,
    MIN(c.quality_score) as min_quality,
    MAX(c.quality_score) as max_quality,
    SUM(CASE WHEN c.quality_score < 0.6 THEN 1 ELSE 0 END) as low_quality_chunks,
    MAX(c.reindex_count) as max_reindex_count
FROM 
    document_metadata d
LEFT JOIN 
    chunk_embedding_data c ON d.doc_id = c.doc_id
GROUP BY 
    d.doc_id, d.title, d.author
ORDER BY 
    avg_chunk_quality ASC;

-- ========================================
-- Query 2: Healing Effectiveness Analysis
-- Purpose: Track which healing strategies work best for which documents
-- ========================================
SELECT 
    d.doc_id,
    d.title,
    json_extract(h.metrics_json, '$.strategy') as healing_strategy,
    COUNT(*) as healing_count,
    AVG(CAST(json_extract(h.metrics_json, '$.improvement_delta') AS FLOAT)) as avg_improvement,
    MAX(CAST(json_extract(h.metrics_json, '$.improvement_delta') AS FLOAT)) as max_improvement,
    json_extract(h.metrics_json, '$.cost_tokens') as avg_cost
FROM 
    rag_history_and_optimization h
JOIN 
    document_metadata d ON h.target_doc_id = d.doc_id
WHERE 
    h.event_type = 'HEAL'
GROUP BY 
    d.doc_id, healing_strategy
ORDER BY 
    avg_improvement DESC;

-- ========================================
-- Query 3: Query Performance Heatmap
-- Purpose: Identify cold (poor), warm (ok), and hot (excellent) queries
-- ========================================
SELECT 
    d.doc_id,
    d.title,
    h.query_text,
    COUNT(*) as query_frequency,
    AVG(CAST(json_extract(h.metrics_json, '$.avg_accuracy') AS FLOAT)) as accuracy,
    AVG(CAST(json_extract(h.metrics_json, '$.latency_ms') AS FLOAT)) as avg_latency_ms,
    AVG(CAST(json_extract(h.metrics_json, '$.user_feedback') AS FLOAT)) as user_satisfaction,
    CASE 
        WHEN AVG(CAST(json_extract(h.metrics_json, '$.avg_accuracy') AS FLOAT)) < 0.60 THEN 'COLD'
        WHEN AVG(CAST(json_extract(h.metrics_json, '$.avg_accuracy') AS FLOAT)) < 0.85 THEN 'WARM'
        ELSE 'HOT'
    END as quality_category
FROM 
    rag_history_and_optimization h
LEFT JOIN 
    document_metadata d ON h.target_doc_id = d.doc_id
WHERE 
    h.event_type = 'QUERY'
GROUP BY 
    h.query_text
ORDER BY 
    accuracy ASC;

-- ========================================
-- Query 4: Complete RL Agent History
-- Purpose: Track all decisions made by the RL healing agent
-- ========================================
SELECT 
    h.history_id,
    h.timestamp,
    h.event_type,
    d.title,
    h.action_taken as rl_action,
    h.reward_signal,
    json_extract(h.state_before, '$.quality_score') as before_quality,
    json_extract(h.state_after, '$.quality_score') as after_quality,
    json_extract(h.metrics_json, '$.improvement_delta') as improvement,
    h.session_id
FROM 
    rag_history_and_optimization h
LEFT JOIN 
    document_metadata d ON h.target_doc_id = d.doc_id
WHERE 
    h.action_taken IS NOT NULL
ORDER BY 
    h.timestamp DESC;

-- ========================================
-- Query 5: Chunk Quality Issues & Healing Suggestions
-- Purpose: Identify problematic chunks and their recommended healing actions
-- ========================================
SELECT 
    d.doc_id,
    d.title,
    c.chunk_id,
    c.quality_score,
    c.reindex_count,
    json_extract(c.healing_suggestions, '$.reason') as issue,
    json_extract(c.healing_suggestions, '$.strategy') as suggested_action,
    json_extract(c.healing_suggestions, '$.suggested_params') as recommended_params,
    json_extract(c.healing_suggestions, '$.expected_improvement') as expected_improvement,
    json_extract(c.healing_suggestions, '$.confidence') as confidence
FROM 
    chunk_embedding_data c
JOIN 
    document_metadata d ON c.doc_id = d.doc_id
WHERE 
    c.quality_score < 0.7
ORDER BY 
    c.quality_score ASC;

-- ========================================
-- Query 6: System-Wide Performance Metrics
-- Purpose: Get overall system health and performance
-- ========================================
SELECT 
    COUNT(DISTINCT target_doc_id) as total_docs_queried,
    COUNT(DISTINCT CASE WHEN event_type = 'QUERY' THEN history_id END) as total_queries,
    COUNT(DISTINCT CASE WHEN event_type = 'HEAL' THEN history_id END) as total_healings,
    AVG(CASE WHEN event_type = 'QUERY' THEN CAST(json_extract(metrics_json, '$.avg_accuracy') AS FLOAT) END) as system_accuracy,
    AVG(CASE WHEN event_type = 'QUERY' THEN CAST(json_extract(metrics_json, '$.latency_ms') AS FLOAT) END) as avg_latency,
    SUM(CASE WHEN event_type = 'HEAL' THEN CAST(json_extract(metrics_json, '$.improvement_delta') AS FLOAT) ELSE 0 END) as total_improvement,
    MIN(timestamp) as system_start_time,
    MAX(timestamp) as last_activity
FROM 
    rag_history_and_optimization;

-- ========================================
-- Query 7: RL Agent Performance Over Time
-- Purpose: Track how well the RL agent is learning and improving
-- ========================================
SELECT 
    strftime('%Y-%m-%d', h.timestamp) as date,
    COUNT(*) as decisions_made,
    AVG(h.reward_signal) as avg_reward,
    COUNT(DISTINCT h.session_id) as sessions,
    json_group_array(DISTINCT h.action_taken) as actions_used,
    SUM(CASE WHEN h.reward_signal > 0.7 THEN 1 ELSE 0 END) as high_reward_decisions,
    SUM(CASE WHEN h.reward_signal < 0.3 THEN 1 ELSE 0 END) as low_reward_decisions
FROM 
    rag_history_and_optimization h
WHERE 
    h.action_taken IS NOT NULL
GROUP BY 
    date
ORDER BY 
    date DESC;

-- ========================================
-- Query 8: Document Metadata Complete Picture
-- Purpose: See all metadata for a specific document (including JSON fields)
-- ========================================
WITH document_info AS (
    SELECT 
        d.doc_id,
        d.title,
        d.author,
        d.source,
        d.summary,
        d.rbac_namespace,
        d.chunk_strategy,
        d.chunk_size_char,
        d.overlap_char,
        d.metadata_json,
        d.last_ingested
    FROM document_metadata d
    WHERE d.doc_id = 'doc_001' -- Replace with actual doc_id
)
SELECT 
    di.*,
    json_extract(di.metadata_json, '$.categories') as categories,
    json_extract(di.metadata_json, '$.keywords') as keywords,
    json_extract(di.metadata_json, '$.doc_type') as doc_type,
    json_extract(di.metadata_json, '$.version') as version,
    json_extract(di.metadata_json, '$.tags') as tags
FROM 
    document_info di;

-- ========================================
-- Query 9: Most Effective Healing Strategies
-- Purpose: Identify which healing strategies provide best ROI
-- ========================================
SELECT 
    json_extract(h.metrics_json, '$.strategy') as strategy,
    COUNT(*) as times_applied,
    AVG(CAST(json_extract(h.metrics_json, '$.improvement_delta') AS FLOAT)) as avg_improvement,
    SUM(CAST(json_extract(h.metrics_json, '$.cost_tokens') AS FLOAT)) as total_cost,
    AVG(CAST(json_extract(h.metrics_json, '$.cost_tokens') AS FLOAT)) as avg_cost_per_application,
    (
        AVG(CAST(json_extract(h.metrics_json, '$.improvement_delta') AS FLOAT)) / 
        NULLIF(AVG(CAST(json_extract(h.metrics_json, '$.cost_tokens') AS FLOAT)), 0)
    ) as roi_ratio
FROM 
    rag_history_and_optimization h
WHERE 
    h.event_type = 'HEAL'
GROUP BY 
    strategy
ORDER BY 
    roi_ratio DESC;

-- ========================================
-- Query 10: Synthetic Test Results & Accuracy
-- Purpose: Track how well the system performs on synthetic test questions
-- ========================================
SELECT 
    d.doc_id,
    d.title,
    COUNT(*) as tests_run,
    AVG(CAST(json_extract(h.metrics_json, '$.accuracy') AS FLOAT)) as avg_accuracy,
    AVG(CAST(json_extract(h.metrics_json, '$.bleu_score') AS FLOAT)) as avg_bleu,
    AVG(CAST(json_extract(h.metrics_json, '$.latency_ms') AS FLOAT)) as avg_latency,
    SUM(CASE WHEN CAST(json_extract(h.metrics_json, '$.accuracy') AS FLOAT) > 0.9 THEN 1 ELSE 0 END) as excellent_results,
    SUM(CASE WHEN CAST(json_extract(h.metrics_json, '$.accuracy') AS FLOAT) < 0.7 THEN 1 ELSE 0 END) as poor_results
FROM 
    rag_history_and_optimization h
LEFT JOIN 
    document_metadata d ON h.target_doc_id = d.doc_id
WHERE 
    h.event_type = 'SYNTHETIC_TEST'
GROUP BY 
    d.doc_id, d.title
ORDER BY 
    avg_accuracy DESC;
