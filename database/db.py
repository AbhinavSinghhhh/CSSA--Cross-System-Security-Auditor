import sqlite3
import json
import logging
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
import datetime

from core.models import (
    AuditResult, Finding, BaselineItem, SystemInfo, AuditScore, CategoryScore,
    Severity, FindingStatus, RiskLevel, AuditMode
)
from database.schema import ALL_TABLES

logger = logging.getLogger(__name__)

# Fallback path function if utils.paths is missing or not fully implemented
def get_fallback_db_path() -> Path:
    # We create a local db in the project directory as fallback
    db_dir = Path(__file__).parent.parent / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "cssa.db"

try:
    from utils.paths import get_db_path
except ImportError:
    get_db_path = get_fallback_db_path

class DatabaseManager:
    """Manages SQLite database connections and operations for CSSA."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path if db_path else get_db_path()
        self._lock = threading.Lock()
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.initialize()
        except Exception as exc:
            fallback = get_fallback_db_path()
            if self.db_path != fallback:
                logger.warning(f"Failed to initialize database at {self.db_path} ({exc}), falling back to {fallback}")
                self.db_path = fallback
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                self.initialize()
            else:
                raise

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-safe database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        """Initialize the database tables."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for create_statement in ALL_TABLES:
                        cursor.execute(create_statement)
                    conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
            except sqlite3.Error as e:
                logger.error(f"Failed to initialize database: {e}")
                raise

    def save_audit(self, audit: AuditResult) -> None:
        """Store an audit result and its findings."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Convert to JSON for full storage
                    # Using a simple dict conversion here
                    import dataclasses
                    def default_encoder(o):
                        if dataclasses.is_dataclass(o):
                            return dataclasses.asdict(o)
                        if isinstance(o, (Severity, FindingStatus, RiskLevel, AuditMode)):
                            return o.value
                        if isinstance(o, datetime.datetime):
                            return o.isoformat()
                        return str(o)

                    try:
                        data_json = json.dumps(dataclasses.asdict(audit), default=default_encoder)
                    except Exception as e:
                        logger.error(f"Failed to serialize audit for DB: {e}")
                        data_json = "{}"

                    score_val = audit.score.overall_score if audit.score else 0
                    risk_val = audit.score.risk_level.value if audit.score and audit.score.risk_level else "UNKNOWN"

                    cursor.execute(
                        '''
                        INSERT INTO audits 
                        (id, timestamp, hostname, os, os_version, username, score, risk_level, mode, data_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (
                            audit.id,
                            audit.timestamp,
                            audit.system_info.hostname if audit.system_info else "",
                            audit.system_info.os_name if audit.system_info else "",
                            audit.system_info.os_version if audit.system_info else "",
                            audit.system_info.current_user if audit.system_info else "",
                            score_val,
                            risk_val,
                            audit.mode.value if audit.mode else "",
                            data_json
                        )
                    )

                    for finding in audit.findings:
                        cursor.execute(
                            '''
                            INSERT INTO findings 
                            (id, audit_id, rule_id, category, severity, status, title, description, evidence, recommendation, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''',
                            (
                                finding.id,
                                audit.id,
                                finding.rule_id,
                                finding.category,
                                finding.severity.value if finding.severity else "",
                                finding.status.value if finding.status else "",
                                finding.title,
                                finding.description,
                                finding.evidence,
                                finding.recommendation,
                                finding.timestamp
                            )
                        )
                    conn.commit()
                logger.info(f"Saved audit {audit.id} to database")
            except sqlite3.Error as e:
                logger.error(f"Failed to save audit: {e}")
                raise

    def get_audits(self) -> List[Dict[str, Any]]:
        """Retrieve audit history summary."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        '''
                        SELECT id, timestamp, hostname, os, os_version, username, score, risk_level, mode 
                        FROM audits 
                        ORDER BY timestamp DESC
                        '''
                    )
                    return [dict(row) for row in cursor.fetchall()]
            except sqlite3.Error as e:
                logger.error(f"Failed to get audits: {e}")
                return []

    def get_audit(self, audit_id: str) -> Optional[AuditResult]:
        """Retrieve full audit by ID, re-hydrated into dataclass structures."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT data_json, score, risk_level FROM audits WHERE id = ?", (audit_id,))
                    row = cursor.fetchone()
                    if row and row['data_json']:
                        try:
                            data = json.loads(row['data_json'])
                            audit = AuditResult.from_dict(data)
                            # Ensure score is fully populated
                            if not audit.score or not audit.score.category_scores:
                                from core.scoring import ScoringSystem
                                scoring = ScoringSystem()
                                audit.score = scoring.calculate_score(audit.findings)
                            return audit
                        except Exception as e:
                            logger.error(f"Failed to parse audit JSON: {e}")
                    return None
            except sqlite3.Error as e:
                logger.error(f"Failed to get audit {audit_id}: {e}")
                return None

    def get_findings(self, audit_id: str) -> List[Finding]:
        """Retrieve findings for an audit."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM findings WHERE audit_id = ?", (audit_id,))
                    results = []
                    for row in cursor.fetchall():
                        try:
                            f = Finding(
                                id=row['id'],
                                rule_id=row['rule_id'],
                                title=row['title'],
                                category=row['category'],
                                severity=Severity(row['severity']) if row['severity'] else Severity.INFO,
                                status=FindingStatus(row['status']) if row['status'] else FindingStatus.UNAVAILABLE,
                                platform="",  # Platform info stored in parent audit
                                description=row['description'],
                                evidence=row['evidence'],
                                rationale="",
                                recommendation=row['recommendation'],
                                timestamp=row['timestamp']
                            )
                            results.append(f)
                        except ValueError as ve:
                            logger.warning(f"Error mapping finding enum: {ve}")
                    return results
            except sqlite3.Error as e:
                logger.error(f"Failed to get findings for audit {audit_id}: {e}")
                return []

    def save_baseline(self, name: str, audit: AuditResult, items: List[BaselineItem]) -> None:
        """Save a new baseline."""
        with self._lock:
            try:
                baseline_id = str(uuid.uuid4())
                timestamp = datetime.datetime.now().isoformat()
                
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        '''
                        INSERT INTO baselines (id, name, timestamp, hostname, os, audit_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''',
                        (
                            baseline_id,
                            name,
                            timestamp,
                            audit.system_info.hostname if audit.system_info else "",
                            audit.system_info.os_name if audit.system_info else "",
                            audit.id
                        )
                    )
                    
                    for item in items:
                        cursor.execute(
                            '''
                            INSERT INTO baseline_items (baseline_id, category, key, value, details)
                            VALUES (?, ?, ?, ?, ?)
                            ''',
                            (
                                baseline_id,
                                item.category,
                                item.key,
                                item.value,
                                item.details
                            )
                        )
                    conn.commit()
                logger.info(f"Saved baseline {name} ({baseline_id})")
            except sqlite3.Error as e:
                logger.error(f"Failed to save baseline: {e}")
                raise

    def get_baselines(self) -> List[Dict[str, Any]]:
        """Get all baselines summary."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM baselines ORDER BY timestamp DESC")
                    return [dict(row) for row in cursor.fetchall()]
            except sqlite3.Error as e:
                logger.error(f"Failed to get baselines: {e}")
                return []

    def get_baseline_items(self, baseline_id: str) -> List[BaselineItem]:
        """Get items for a baseline."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM baseline_items WHERE baseline_id = ?", (baseline_id,))
                    return [
                        BaselineItem(
                            category=row['category'],
                            key=row['key'],
                            value=row['value'],
                            details=row['details']
                        ) for row in cursor.fetchall()
                    ]
            except sqlite3.Error as e:
                logger.error(f"Failed to get baseline items: {e}")
                return []

    def delete_audit(self, audit_id: str) -> None:
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM audits WHERE id = ?", (audit_id,))
                    conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Failed to delete audit {audit_id}: {e}")
                raise

    def delete_baseline(self, baseline_id: str) -> None:
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM baselines WHERE id = ?", (baseline_id,))
                    conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Failed to delete baseline {baseline_id}: {e}")
                raise

    def get_setting(self, key: str, default: str = '') -> str:
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
                    row = cursor.fetchone()
                    return row['value'] if row else default
            except sqlite3.Error as e:
                logger.error(f"Failed to get setting {key}: {e}")
                return default

    def set_setting(self, key: str, value: str) -> None:
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                        (key, value)
                    )
                    conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Failed to set setting {key}: {e}")
                raise
