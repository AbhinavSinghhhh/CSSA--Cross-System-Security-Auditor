"""SQL schema definitions for the CSSA database."""

SCHEMA_VERSION = 1

CREATE_AUDITS_TABLE = """
CREATE TABLE IF NOT EXISTS audits (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    hostname TEXT,
    os TEXT,
    os_version TEXT,
    username TEXT,
    score INTEGER,
    risk_level TEXT,
    mode TEXT,
    data_json TEXT
)
"""

CREATE_FINDINGS_TABLE = """
CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL,
    rule_id TEXT,
    category TEXT,
    severity TEXT,
    status TEXT,
    title TEXT,
    description TEXT,
    evidence TEXT,
    recommendation TEXT,
    timestamp TEXT,
    FOREIGN KEY(audit_id) REFERENCES audits(id) ON DELETE CASCADE
)
"""

CREATE_BASELINES_TABLE = """
CREATE TABLE IF NOT EXISTS baselines (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    hostname TEXT,
    os TEXT,
    audit_id TEXT
)
"""

CREATE_BASELINE_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS baseline_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    baseline_id TEXT NOT NULL,
    category TEXT,
    key TEXT,
    value TEXT,
    details TEXT,
    FOREIGN KEY(baseline_id) REFERENCES baselines(id) ON DELETE CASCADE
)
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
"""

ALL_TABLES = [
    CREATE_AUDITS_TABLE,
    CREATE_FINDINGS_TABLE,
    CREATE_BASELINES_TABLE,
    CREATE_BASELINE_ITEMS_TABLE,
    CREATE_SETTINGS_TABLE
]
