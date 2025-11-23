"""Create RL-specific metadata tables for Q-Learning"""

def run(conn):
    # Q-Table Storage Table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS rl_q_table (
        q_id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_key TEXT NOT NULL,
        action TEXT NOT NULL,
        q_value REAL DEFAULT 0.0,
        visits INTEGER DEFAULT 0,
        last_updated TEXT DEFAULT (datetime('now')),
        UNIQUE(state_key, action)
    )
    ''')
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_rl_q_table_state ON rl_q_table(state_key)
    ''')
    
    # Episodes Tracking Table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS rl_episodes (
        episode_id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id TEXT NOT NULL,
        episode_number INTEGER,
        initial_state TEXT,
        final_state TEXT,
        total_reward REAL,
        total_steps INTEGER,
        status TEXT,
        started_at TEXT DEFAULT (datetime('now')),
        completed_at TEXT,
        duration_ms INTEGER
    )
    ''')
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_rl_episodes_doc ON rl_episodes(document_id)
    ''')
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_rl_episodes_status ON rl_episodes(status)
    ''')
    
    # Experience Replay Buffer Table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS rl_experience_buffer (
        experience_id INTEGER PRIMARY KEY AUTOINCREMENT,
        episode_id INTEGER,
        step_number INTEGER,
        state_key TEXT NOT NULL,
        action TEXT NOT NULL,
        reward REAL,
        next_state_key TEXT,
        done INTEGER DEFAULT 0,
        timestamp TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (episode_id) REFERENCES rl_episodes(episode_id) ON DELETE CASCADE
    )
    ''')
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_rl_exp_episode ON rl_experience_buffer(episode_id)
    ''')
    
    # RL Optimization History Table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS rl_optimizations (
        optimization_id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id TEXT NOT NULL,
        episode_id INTEGER,
        action_taken TEXT NOT NULL,
        metrics_before TEXT,
        metrics_after TEXT,
        quality_delta REAL,
        cost_delta REAL,
        latency_delta REAL,
        reward REAL,
        successful INTEGER DEFAULT 1,
        timestamp TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (episode_id) REFERENCES rl_episodes(episode_id) ON DELETE CASCADE
    )
    ''')
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_rl_opt_doc ON rl_optimizations(document_id)
    ''')
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_rl_opt_action ON rl_optimizations(action_taken)
    ''')
    
    # Policy Metrics Table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS rl_policy_metrics (
        metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
        episode_id INTEGER,
        avg_reward REAL,
        max_reward REAL,
        min_reward REAL,
        epsilon REAL,
        alpha REAL,
        gamma REAL,
        total_episodes INTEGER,
        exploration_rate REAL,
        exploitation_rate REAL,
        timestamp TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (episode_id) REFERENCES rl_episodes(episode_id) ON DELETE CASCADE
    )
    ''')
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_rl_policy_episode ON rl_policy_metrics(episode_id)
    ''')
    
    # Action Performance Summary Table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS rl_action_stats (
        action_id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_name TEXT NOT NULL UNIQUE,
        total_taken INTEGER DEFAULT 0,
        total_reward REAL DEFAULT 0.0,
        avg_reward REAL DEFAULT 0.0,
        success_count INTEGER DEFAULT 0,
        success_rate REAL DEFAULT 0.0,
        avg_quality_improvement REAL DEFAULT 0.0,
        avg_cost_savings REAL DEFAULT 0.0,
        last_used TEXT,
        updated_at TEXT DEFAULT (datetime('now'))
    )
    ''')
    
    conn.commit()
