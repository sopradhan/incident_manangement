#!/usr/bin/env python3
"""
RL HEALING AGENT - QUICK REFERENCE & USAGE
"""

usage_guide = """
╔════════════════════════════════════════════════════════════════════════════╗
║         RL HEALING AGENT - QUICK REFERENCE & USAGE GUIDE                   ║
╚════════════════════════════════════════════════════════════════════════════╝


WHERE IS IT USED?
═══════════════════════════════════════════════════════════════════════════

File: src/incident_iq/rag/agents/langgraph_agent/langgraph_rag_agent.py

Specifically in the _build_retrieval_graph() method:

    def healing_decision_node(state):
        if self.rl_healing_agent and state.get("doc_id"):
            # Build state
            rl_state = RLState(
                quality_score=...,
                query_accuracy=...,
                chunk_count=...,
                avg_token_cost=...,
                reindex_count=...,
                last_healing_delta=...,
                query_frequency=...,
                user_feedback=...
            )
            
            # GET RL DECISION
            recommendation = self.rl_healing_agent.decide_action(
                rl_state, 
                state.get("doc_id")
            )
            
            # APPLY ACTION
            if recommendation.action != "SKIP":
                apply_healing_action(recommendation)
            
            # RECORD REWARD
            actual_reward = measure_improvement()
            self.rl_healing_agent.observe_reward(
                recommendation, 
                actual_reward, 
                state.get("session_id")
            )


HOW TO USE IT DIRECTLY
═══════════════════════════════════════════════════════════════════════════

Example 1: Get RL Recommendation
────────────────────────────────

    from incident_iq.rag.agents.healing_agent.rl_healing_agent import (
        RLHealingAgent, RLState
    )
    
    # Initialize
    agent = RLHealingAgent(db_path="chroma_db/rag.db")
    
    # Create state
    state = RLState(
        quality_score=0.55,
        query_accuracy=0.60,
        chunk_count=4,
        avg_token_cost=1800.0,
        reindex_count=1,
        last_healing_delta=0.10,
        query_frequency=5,
        user_feedback=0.65
    )
    
    # Get recommendation
    action = agent.decide_action(state, doc_id="doc_123")
    
    print(f"Recommended: {action.action}")
    print(f"Params: {action.params}")
    print(f"Improvement: {action.estimated_improvement}")
    print(f"Confidence: {action.confidence}")


Example 2: Learn from Outcome
──────────────────────────────

    # After applying the action and seeing results
    actual_improvement = 0.12  # Quality went from 0.55 to 0.67
    actual_cost = 450  # tokens spent
    
    # Calculate reward
    reward = actual_improvement - (actual_cost / 1000)  # Normalize cost
    
    # Update RL agent learning
    agent.observe_reward(
        action=action,
        actual_reward=reward,
        session_id="session_abc123"
    )


Example 3: Get Learning Statistics
───────────────────────────────────

    stats = agent.get_learning_stats()
    
    print(f"Total learning episodes: {stats['total_episodes']}")
    print(f"Current epsilon: {stats['epsilon']}")
    print(f"\nAction effectiveness:")
    
    for action_name, metrics in stats['action_stats'].items():
        print(f"\n{action_name}:")
        print(f"  Times used: {metrics['count']}")
        print(f"  Avg reward: {metrics['avg_reward']:.2f}")
        print(f"  Success rate: {metrics['success_rate']:.1%}")


RL ACTIONS REFERENCE
═══════════════════════════════════════════════════════════════════════════

1. SKIP
   └─ No action taken (document already good enough)
      ├─ When: quality_score > 0.75
      ├─ Cost: 0 tokens
      ├─ Risk: Very low
      └─ Best for: Already high-quality documents

2. OPTIMIZE
   └─ Adjust chunking parameters (chunk_size, overlap)
      ├─ When: 0.6 < quality_score < 0.75
      ├─ Cost: ~500 tokens
      ├─ Expected improvement: 8-15%
      ├─ Parameters:
      │  ├─ new_chunk_size: 256 or 384 (vs current 512)
      │  └─ new_overlap: ~10% of chunk size
      └─ Best for: Moderate quality issues with cost constraints

3. REINDEX
   └─ Re-compute embeddings with same parameters
      ├─ When: quality_score < 0.65 AND reindex_count < 3
      ├─ Cost: ~300 tokens
      ├─ Expected improvement: 5-12% (diminishing returns)
      ├─ Parameters:
      │  ├─ clear_cache: true
      │  └─ recompute_embeddings: true
      └─ Best for: Stale embeddings, minor quality issues

4. RE_EMBED
   └─ Use different embedding model (e.g., mistral instead of default)
      ├─ When: quality_score < 0.5 (critical)
      ├─ Cost: ~800 tokens
      ├─ Expected improvement: 20-25% (high risk, high reward)
      ├─ Parameters:
      │  ├─ new_model: "mistral" or other model
      │  └─ preserve_old_embeddings: true (can roll back)
      └─ Best for: Severely degraded quality, last resort


STATE PARAMETERS EXPLANATION
═══════════════════════════════════════════════════════════════════════════

quality_score (0.0-1.0)
├─ What: Overall quality of document embeddings
├─ Source: Calculated from retrieval success rate
├─ Range: 0.0 (terrible) to 1.0 (perfect)
└─ Impact: PRIMARY factor in action selection

query_accuracy (0.0-1.0)
├─ What: How well answers match queries
├─ Source: Semantic similarity of answer to question
├─ Calculated from: BLEU score, cosine similarity
└─ Impact: Confirms quality_score assessment

chunk_count
├─ What: Number of chunks in document
├─ Source: From document metadata
├─ Typical: 4-50 (depends on doc size)
└─ Impact: Affects reindexing cost estimate

avg_token_cost
├─ What: Average tokens spent per query for this document
├─ Source: Tracked in rag_history_and_optimization
├─ Typical: 500-2000 tokens
└─ Impact: Cost-benefit calculation for actions

reindex_count
├─ What: How many times this document has been reindexed
├─ Source: Tracking in database
├─ Impact: REINDEX becomes less effective after 2-3 times

last_healing_delta
├─ What: Quality improvement from last healing action
├─ Source: Difference before/after last optimization
├─ Range: -0.5 to +0.5
└─ Impact: Confidence in effectiveness of healing

query_frequency
├─ What: How often queries target this document
├─ Source: Tracked in rag_history_and_optimization
├─ Impact: High-frequency docs worth optimizing

user_feedback (0.0-1.0)
├─ What: User satisfaction with answers
├─ Source: Optional user ratings
├─ Impact: Immediate signal of quality


REWARDS & LEARNING
═══════════════════════════════════════════════════════════════════════════

Reward Formula:
    reward = quality_improvement - (token_cost / scaling_factor)

Example:
    ├─ Quality before: 0.55
    ├─ Quality after: 0.67
    ├─ Improvement: 0.12
    ├─ Tokens spent: 500
    ├─ Scaled cost: 0.5
    └─ REWARD: 0.12 - 0.5 = -0.38 (negative, didn't work well)

Q-Learning Updates:
    ├─ For each action tried, update its average reward
    ├─ Negative rewards → action deprioritized
    ├─ Positive rewards → action prioritized
    └─ Over time, agent learns optimal actions

Epsilon Decay:
    ├─ Starts: ε = 0.3 (30% random exploration)
    ├─ Decay: ε *= 0.99 per episode
    ├─ After 100 episodes: ε ≈ 0.05
    └─ Final: Agent exploits learned optimal actions


DEBUGGING & MONITORING
═══════════════════════════════════════════════════════════════════════════

Check Learning Progress:

    stats = agent.get_learning_stats()
    
    if stats['total_episodes'] > 0:
        print(f"Learning progress: {stats['total_episodes']} episodes")
        print(f"Exploration rate: {stats['epsilon']:.1%}")
        
        best_action = max(
            stats['action_stats'].items(),
            key=lambda x: x[1]['avg_reward']
        )
        print(f"Best action: {best_action[0]}")


Common Issues:

1. Agent always choosing SKIP
   └─ Likely: Quality scores are consistently high
   └─ Solution: Check if documents are actually good

2. Agent always exploring (random actions)
   └─ Likely: Epsilon not decaying
   └─ Solution: Verify epsilon decay in observe_reward()

3. Low success rate for OPTIMIZE
   └─ Likely: Chunk size recommendations not optimal
   └─ Solution: Tune the score adjustments in _get_best_action()

4. RE_EMBED not improving quality
   └─ Likely: Embedding model not different enough
   └─ Solution: Try different model or revert with fallback


INTEGRATION CHECKLIST
═══════════════════════════════════════════════════════════════════════════

When using RL Healing Agent:

□ Initialize with correct db_path (chroma_db/rag.db)
□ Build RLState from current document metrics
□ Call decide_action() to get recommendation
□ Apply the recommended action
□ Track actual improvement (before/after quality)
□ Call observe_reward() to update learning
□ Check learning stats periodically
□ Monitor for action effectiveness drift
□ Adjust reward scaling if needed
□ Save/load agent state for persistence (if needed)

"""

print(usage_guide)
