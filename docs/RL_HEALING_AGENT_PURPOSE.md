#!/usr/bin/env python3
"""
PURPOSE & ARCHITECTURE: RL Healing Agent
File: src/incident_iq/rag/agents/healing_agent/rl_healing_agent.py
"""

purpose = """
╔════════════════════════════════════════════════════════════════════════════╗
║            RL HEALING AGENT - PURPOSE & ARCHITECTURE                       ║
╚════════════════════════════════════════════════════════════════════════════╝

OVERALL PURPOSE
═══════════════════════════════════════════════════════════════════════════

The RLHealingAgent is a Reinforcement Learning-based system that intelligently
optimizes RAG (Retrieval-Augmented Generation) system performance by:

1. MONITORING: Tracking document quality, query accuracy, and token costs
2. DECIDING: Using RL to decide when/how to optimize the system
3. LEARNING: Improving decision-making over time based on outcomes
4. BALANCING: Maximizing quality while minimizing computational cost

KEY COMPONENTS
═══════════════════════════════════════════════════════════════════════════

1. STATE (RLState Dataclass)
   ├─ quality_score: Overall document/chunk quality (0.0-1.0)
   ├─ query_accuracy: How well queries are answered
   ├─ chunk_count: Number of chunks in document
   ├─ avg_token_cost: Average tokens spent per query
   ├─ reindex_count: How many times document has been reindexed
   ├─ last_healing_delta: Quality improvement from last healing
   ├─ query_frequency: How often this document is queried
   └─ user_feedback: User satisfaction score

2. ACTIONS (4 possible healing actions)
   ├─ SKIP: Do nothing (document already good quality)
   ├─ OPTIMIZE: Adjust chunking parameters (size, overlap)
   ├─ REINDEX: Re-compute embeddings with same parameters
   └─ RE_EMBED: Use different embedding model (e.g., switch to better one)

3. REWARD CALCULATION
   ├─ Positive: Quality improvement + decreased cost
   ├─ Negative: Cost without sufficient quality improvement
   └─ Formula: (Quality_Improvement - Token_Cost) * Confidence

4. LEARNING MECHANISM
   ├─ Q-Learning: Updates value estimates for state-action pairs
   ├─ Epsilon-Greedy: Balances exploration vs exploitation
   ├─ Action History: Tracks effectiveness of each action type
   └─ Continuous Improvement: Better decisions over time


WORKFLOW: HOW IT WORKS
═══════════════════════════════════════════════════════════════════════════

Step 1: OBSERVE STATE
   LangGraph Agent monitors document:
   └─ quality_score, query patterns, cost metrics

Step 2: CONSULT RL AGENT
   LangGraph calls: rl_healing_agent.decide_action(state, doc_id)
   
   RL Agent Decision Process:
   ├─ Epsilon-Greedy Strategy:
   │  ├─ With probability ε (e.g., 0.3): Explore random action
   │  └─ With probability 1-ε: Exploit best known action
   │
   └─ Best Action Selection:
      ├─ Score each action based on:
      │  ├─ Historical effectiveness
      │  ├─ Current state characteristics
      │  └─ Action-specific adjustments
      └─ Return highest-scoring action

Step 3: RECOMMEND ACTION
   Returns RLAction with:
   ├─ action: Which action to take (SKIP, OPTIMIZE, etc.)
   ├─ params: Specific parameters (chunk size, model, etc.)
   ├─ estimated_improvement: Expected quality gain
   ├─ estimated_cost: Token cost
   └─ confidence: How sure the agent is (0.0-1.0)

Step 4: EXECUTE ACTION
   LangGraph applies the action:
   ├─ SKIP: No changes
   ├─ OPTIMIZE: Re-chunk with new parameters
   ├─ REINDEX: Recompute embeddings
   └─ RE_EMBED: Use different embedding model

Step 5: OBSERVE REWARD
   Track outcome and update learning:
   └─ rl_healing_agent.observe_reward(action, actual_reward, session_id)
      ├─ Update Q-values
      ├─ Update action statistics
      ├─ Decay epsilon (explore less over time)
      └─ Learn what works best


DECISION LOGIC: ACTION SELECTION
═══════════════════════════════════════════════════════════════════════════

For each document state, the agent scores actions:

SKIP:
├─ Best When: quality_score > 0.75
├─ Score Boost: +1.0 for high quality
├─ Score Penalty: -1.0 for low quality
└─ Logic: Don't waste resources on already-good documents

OPTIMIZE:
├─ Best When: 0.6 > quality_score < 0.75
├─ Score Boost: +1.5 if quality < 0.6 AND cost < 2000 tokens
├─ Score Penalty: -0.5 if quality > 0.75
└─ Logic: Adjust chunk size to balance quality and cost

REINDEX:
├─ Best When: quality_score < 0.65 AND reindex_count < 3
├─ Score Boost: +1.0 for first few reindexes
├─ Score Penalty: -1.0 if already reindexed 3+ times
└─ Logic: Fresh embeddings can help, but diminishing returns

RE_EMBED:
├─ Best When: quality_score < 0.5 (desperate times)
├─ Score Boost: +2.0 if quality critical
├─ Score Penalty: -1.5 if cost > 1000 tokens
└─ Logic: Last resort - use better embedding model


LEARNING OVER TIME
═══════════════════════════════════════════════════════════════════════════

Action History Tracking:
├─ For SKIP, OPTIMIZE, REINDEX, RE_EMBED:
│  ├─ count: Number of times used
│  ├─ total_reward: Sum of all rewards
│  └─ avg_reward: Average reward per use

Q-Values Storage:
├─ Store state_action_pair -> value mappings
└─ Use to make better decisions in similar situations

Epsilon Decay:
├─ Start: ε = 0.3 (30% exploration)
├─ Over Time: Gradually decrease ε
└─ End: ε ≈ 0.05 (mostly exploitation, minimal exploration)

Convergence:
└─ As more queries happen, agent converges to optimal actions


INTEGRATION WITH LANGGRAPH
═══════════════════════════════════════════════════════════════════════════

LangGraph Retrieval Graph includes:

1. Retrieve Context Node
   └─ Get initial results

2. Rerank Context Node
   └─ Order by relevance

3. **Healing Decision Node** ← RL AGENT CALLED HERE
   ├─ Check retrieval quality
   ├─ Call rl_healing_agent.decide_action()
   ├─ Get recommendation (SKIP, OPTIMIZE, REINDEX, RE_EMBED)
   └─ If recommendation != SKIP, apply healing action

4. Generate Answer Node
   └─ Create final answer

5. Record Reward Node ← RL AGENT UPDATED HERE
   ├─ Measure actual quality improvement
   └─ Call rl_healing_agent.observe_reward()


EXAMPLE SCENARIO
═══════════════════════════════════════════════════════════════════════════

Query about "Incident Severity Levels":

1. STATE OBSERVATION
   ├─ quality_score: 0.55 (poor)
   ├─ query_accuracy: 0.60 (weak)
   ├─ avg_token_cost: 1800 tokens
   ├─ reindex_count: 1
   └─ query_frequency: 5

2. RL DECISION
   ├─ Epsilon check: 0.2 < 0.3 → Exploit
   ├─ Score SKIP: -0.5 (quality too low)
   ├─ Score OPTIMIZE: +1.5 (perfect conditions)
   ├─ Score REINDEX: +1.0 (reasonable)
   ├─ Score RE_EMBED: +0.8 (risky, expensive)
   └─ **CHOOSE: OPTIMIZE** (highest score 1.5)

3. ACTION PARAMETERS
   ├─ New chunk size: 256 (smaller)
   ├─ New overlap: 25%
   ├─ Estimated improvement: 0.15 (15%)
   ├─ Estimated cost: 500 tokens
   └─ Confidence: 0.82

4. EXECUTION
   └─ Re-chunk all document chunks with new parameters

5. REWARD OBSERVATION
   ├─ Quality improved to: 0.68 (+0.13)
   ├─ Cost: 450 tokens
   ├─ Reward = 0.13 - 0.45 = -0.32 (didn't break even)
   └─ Update action history: lower score for OPTIMIZE slightly

6. LEARNING
   └─ For similar states, OPTIMIZE may score lower next time


KEY FILES USING RL HEALING AGENT
═══════════════════════════════════════════════════════════════════════════

1. src/incident_iq/rag/agents/langgraph_agent/langgraph_rag_agent.py
   └─ Initializes and calls the RL agent

2. scripts/demo_optimized_rag_with_rl.py
   └─ Demonstrates RL agent in action with test scenarios

3. src/incident_iq/rag/agents/healing_agent/__init__.py
   └─ Exports RLHealingAgent class


CURRENT STATUS
═══════════════════════════════════════════════════════════════════════════

✓ IMPLEMENTED:
  ├─ Epsilon-greedy strategy
  ├─ Q-learning framework
  ├─ Action history tracking
  ├─ State evaluation
  └─ Reward observation

✓ INTEGRATED WITH:
  ├─ LangGraph retrieval pipeline
  ├─ Optimized SQLite schema
  └─ RL learning statistics table

✓ DATABASE TRACKING:
  ├─ rag_history_and_optimization table (event_type='HEAL')
  └─ chunk_embedding_data table (quality_score, healing_suggestions)

⚠ CONSIDERATIONS:
  ├─ Epsilon decay rate affects exploration vs exploitation
  ├─ Reward signal design impacts convergence
  ├─ Large state space may require approximation
  └─ Session-based learning could improve domain transfer
"""

print(purpose)

print("\n" + "="*80)
print("QUICK SUMMARY")
print("="*80)
print("""
The RL Healing Agent is a smart optimizer that learns which healing actions
(SKIP, OPTIMIZE, REINDEX, RE_EMBED) work best for different documents.

It uses Reinforcement Learning (Q-learning + epsilon-greedy) to:
- Monitor document quality and performance
- Make intelligent decisions about when to optimize
- Learn from outcomes to improve future decisions
- Balance quality improvement with computational cost

Think of it as a self-improving system that gets smarter the more queries it handles.
""")
