-- ===========================================================
-- TABLE: AI_Agents
-- PURPOSE:
-- Stores configuration and status of all autonomous AI agents.
-- ===========================================================
DROP TABLE IF EXISTS AI_Agents;
CREATE TABLE AI_Agents (
    agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT UNIQUE NOT NULL,
    agent_category TEXT NOT NULL,
    description TEXT,
    model_name TEXT,
    version TEXT,
    status TEXT DEFAULT 'Active'
        CHECK(status IN
        ('Active',
         'Inactive',
         'Training',
         'Maintenance')),
    health_status TEXT DEFAULT 'Healthy'
        CHECK(health_status IN
        ('Healthy',
         'Warning',
         'Critical')),
    last_execution DATETIME,
    next_execution DATETIME,
    average_response_time REAL DEFAULT 0,
    success_rate REAL DEFAULT 100,
    total_tasks_completed INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- ===========================================================
-- TABLE: AI_Task_Log
-- PURPOSE:
-- Stores every task executed by AI agents.
-- ===========================================================
DROP TABLE IF EXISTS AI_Task_Log;
CREATE TABLE AI_Task_Log (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    task_name TEXT NOT NULL,
    input_source TEXT,
    output_summary TEXT,
    execution_time REAL,
    execution_status TEXT
        CHECK(execution_status IN
        ('Success',
         'Failed',
         'Running',
         'Pending')),
    confidence_score REAL,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id)
        REFERENCES AI_Agents(agent_id)
);
-- ===========================================================
-- TABLE: AI_Decisions
-- PURPOSE:
-- Stores important AI decisions for transparency.
-- ===========================================================
DROP TABLE IF EXISTS AI_Decisions;
CREATE TABLE AI_Decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    decision_type TEXT,
    decision_summary TEXT,
    confidence_score REAL,
    approved_by TEXT DEFAULT 'AI',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id)
        REFERENCES AI_Agents(agent_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_ai_status
ON AI_Agents(status);
CREATE INDEX idx_ai_health
ON AI_Agents(health_status);
CREATE INDEX idx_ai_task_agent
ON AI_Task_Log(agent_id);
CREATE INDEX idx_ai_task_status
ON AI_Task_Log(execution_status);
CREATE INDEX idx_ai_decision_agent
ON AI_Decisions(agent_id);
CREATE INDEX idx_ai_decision_date
ON AI_Decisions(created_at);