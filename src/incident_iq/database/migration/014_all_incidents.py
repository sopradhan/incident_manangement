def run(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS all_incidents (
        id TEXT PRIMARY KEY,                    -- INC-YYYYMMDDHHMMSS
        source TEXT ,                   -- 'pagerduty', 'jira', 'slack'

        -- Common fields
        title TEXT ,                    -- Incident title or summary
        description TEXT,                       -- Optional details or message content
        priority TEXT,                          -- critical, high, medium, low
        urgency TEXT,                           -- high, low (PagerDuty)
        status TEXT DEFAULT 'open',             -- open, triggered, acknowledged, resolved, closed
        created_at TEXT ,               -- ISO timestamp
        last_updated TEXT,                      -- For sync/update tracking
        reporter TEXT,                          -- User who created or reported the incident
        assigned_to TEXT,                       -- Owner or responder handling the incident

        -- Nullable fields —

        -- PagerDuty-specific
        pd_incident_id TEXT,                    -- PagerDuty incident ID (PD-YYYYMMDDHHMMSS)
        pd_service_id TEXT,                     -- PagerDuty service ID
        pd_escalation_policy TEXT,              -- Escalation policy name or ID
        pd_html_url TEXT,                       -- Direct PagerDuty incident URL

        -- Jira-specific
        jira_ticket_id TEXT,                    -- JIRA ticket ID (JIRA-YYYYMMDDHHMMSS)
        jira_project TEXT,                      -- JIRA project key (e.g., OPS, PROD)
        jira_issue_type TEXT,                   -- Bug, Task, Incident, etc.
        jira_url TEXT,                          -- Link to Jira ticket

        -- Slack-specific
        slack_channel TEXT,                     -- Slack channel (e.g., #incidents-high)
        slack_thread_ts TEXT,                   -- Slack thread timestamp
        slack_user TEXT,                        -- Slack user who posted the alert
        slack_permalink TEXT                    -- Direct link to the message/thread
    );
    ''')
    conn.commit()


