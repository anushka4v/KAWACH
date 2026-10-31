"""Audit logging and request history storage for KAWACH / AGENTSHIELD.

Every security decision, whether ALLOW, DENY, or REQUIRE_APPROVAL,
is logged with execution evidence and immutable timestamps.
"""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.database import get_connection


def record_request(
    request_id: str,
    agent_id: str,
    tool: str,
    action: str,
    resource: Optional[str] = None,
    destination: Optional[str] = None,
    arguments: Optional[Dict[str, Any]] = None,
    created_at: Optional[str] = None
) -> None:
    """Inserts a proposed tool request into the requests table."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        ts = created_at or datetime.now(timezone.utc).isoformat()
        cursor.execute(
            """
            INSERT OR REPLACE INTO requests 
            (id, agent_id, tool, action, resource, destination, arguments_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                request_id,
                agent_id,
                tool,
                action,
                resource,
                destination,
                json.dumps(arguments or {}),
                ts
            )
        )
        conn.commit()
    finally:
        conn.close()


def record_audit_event(
    request_id: str,
    agent_id: str,
    tool: str,
    action: str,
    decision: str,
    reason_code: str,
    reason: str,
    execution_status: str,
    resource: Optional[str] = None,
    destination: Optional[str] = None,
    approval_id: Optional[str] = None,
    timestamp: Optional[str] = None
) -> int:
    """Records an authoritative gateway decision and execution status in audit_logs."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        cursor.execute(
            """
            INSERT INTO audit_logs 
            (request_id, agent_id, tool, action, resource, destination, 
             decision, reason_code, reason, execution_status, approval_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                request_id,
                agent_id,
                tool,
                action,
                resource,
                destination,
                decision,
                reason_code,
                reason,
                execution_status,
                approval_id,
                ts
            )
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_audit_logs(
    limit: int = 100,
    decision_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns chronological audit records in reverse chronological order."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if decision_filter and decision_filter.upper() != "ALL":
            cursor.execute(
                """
                SELECT id, request_id, agent_id, tool, action, resource, destination,
                       decision, reason_code, reason, execution_status, approval_id, timestamp
                FROM audit_logs
                WHERE UPPER(decision) = UPPER(?)
                ORDER BY id DESC
                LIMIT ?;
                """,
                (decision_filter, limit)
            )
        else:
            cursor.execute(
                """
                SELECT id, request_id, agent_id, tool, action, resource, destination,
                       decision, reason_code, reason, execution_status, approval_id, timestamp
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?;
                """,
                (limit,)
            )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_requests(limit: int = 100) -> List[Dict[str, Any]]:
    """Returns recent tool request records joined with latest decision."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.id as request_id, r.agent_id, r.tool, r.action, r.resource, r.destination,
                   r.arguments_json, r.created_at,
                   a.decision, a.reason_code, a.reason, a.execution_status
            FROM requests r
            LEFT JOIN (
                SELECT request_id, decision, reason_code, reason, execution_status,
                       ROW_NUMBER() OVER(PARTITION BY request_id ORDER BY id DESC) as rn
                FROM audit_logs
            ) a ON r.id = a.request_id AND a.rn = 1
            ORDER BY r.created_at DESC
            LIMIT ?;
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["arguments"] = json.loads(d.pop("arguments_json", "{}"))
            except Exception:
                d["arguments"] = {}
            result.append(d)
        return result
    finally:
        conn.close()
