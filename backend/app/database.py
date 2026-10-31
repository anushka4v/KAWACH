"""SQLite Database layer for KAWACH / AGENTSHIELD.

Uses parameterised queries strictly.
Manages tables for requests, approvals, and audit_logs.
"""

import os
import sqlite3
from typing import Optional

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "agentshield.db"
)


def get_db_path(custom_path: Optional[str] = None) -> str:
    """Returns database file path, allowing override for tests."""
    return custom_path or os.environ.get("AGENTSHIELD_DB_PATH", DEFAULT_DB_PATH)


def _ensure_parent_dir(path: str) -> None:
    """Creates the database parent directory so a fresh deploy can start clean.

    SQLite creates the database file itself when it is missing; it only needs
    the containing directory to exist.
    """
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a sqlite3 connection with Row factory."""
    path = get_db_path(db_path)
    _ensure_parent_dir(path)
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialises SQLite tables with strict parameterised schemas."""
    path = get_db_path(db_path)
    _ensure_parent_dir(path)
    conn = sqlite3.connect(path)
    try:
        cursor = conn.cursor()
        
        # Requests table: records every proposed tool invocation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT,
                destination TEXT,
                arguments_json TEXT,
                created_at TEXT NOT NULL
            );
        """)

        # Approvals table: binds human approval to payload hash
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT,
                destination TEXT,
                payload_snapshot TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL,
                approver TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT
            );
        """)

        # Audit logs table: chronological security decisions and execution evidence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT,
                destination TEXT,
                decision TEXT NOT NULL,
                reason_code TEXT NOT NULL,
                reason TEXT NOT NULL,
                execution_status TEXT NOT NULL,
                approval_id TEXT,
                timestamp TEXT NOT NULL
            );
        """)
        
        conn.commit()
    finally:
        conn.close()


def clear_db(db_path: Optional[str] = None) -> None:
    """Clears all records for clean demo / test resets."""
    path = get_db_path(db_path)
    _ensure_parent_dir(path)
    conn = sqlite3.connect(path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM audit_logs;")
        cursor.execute("DELETE FROM approvals;")
        cursor.execute("DELETE FROM requests;")
        conn.commit()
    finally:
        conn.close()
