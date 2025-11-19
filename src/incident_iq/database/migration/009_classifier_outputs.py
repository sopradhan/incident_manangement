def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS "classifier_outputs" (
        "id"	INTEGER,
        "payload_id"	TEXT NOT NULL UNIQUE,
        "subscription_id"	TEXT,
        "resource_group"	TEXT,
        "resource_type"	TEXT,
        "resource_name"	TEXT,
        "environment"	TEXT,
        "severity_id"	VARCHAR(10),
        "bert_score"	FLOAT,
        "rule_score"	FLOAT,
        "combined_score"	FLOAT,
        "matched_pattern"	TEXT,
        "is_incident"	SMALLINT DEFAULT 1,
        "source_type"	VARCHAR(50),
        "payload"	TEXT,
        "processed_at"	TIMESTAMP DEFAULT NULL,
        "corrective_action"	TEXT,
        "approved_corrective_action"	TEXT,
        "is_llm_correction_approved"	SMALLINT DEFAULT 0,
        "approved_by"	TEXT,
        "approved_at"	TIMESTAMP,
        "approved_severity"	CHAR,
        "created_at"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        "updated_at"	TIMESTAMP DEFAULT NULL,
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    ''')
    conn.commit()