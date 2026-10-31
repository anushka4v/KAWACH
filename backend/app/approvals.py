"""Human Approval Management for KAWACH / AGENTSHIELD.

Security requirements:
1. Approval is bound to an immutable snapshot and SHA-256 hash of the exact original payload.
2. One-time use: a replay attempt or already-processed approval is refused.
3. Reject never executes any tool.
4. Tampering detection: if stored snapshot hash fails verification, execution is aborted.
5. Persisted in SQLite.
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple, Callable
from app.database import get_connection
from app.audit import record_audit_event
from app.schemas import ApprovalRecord, ApprovalDecision


def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """Computes a deterministic SHA-256 hash of a JSON-serializable dictionary."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def create_pending_approval(
    request_id: str,
    agent_id: str,
    tool: str,
    action: str,
    resource: Optional[str],
    destination: Optional[str],
    arguments: Dict[str, Any],
    reason: str
) -> ApprovalRecord:
    """Creates a new PENDING approval bound to an immutable hash snapshot."""
    approval_id = f"appr_{uuid.uuid4().hex[:12]}"
    now_ts = datetime.now(timezone.utc).isoformat()

    payload_snapshot = {
        "request_id": request_id,
        "agent_id": agent_id,
        "tool": tool,
        "action": action,
        "resource": resource,
        "destination": destination,
        "arguments": arguments
    }
    payload_hash = compute_payload_hash(payload_snapshot)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO approvals 
            (id, request_id, agent_id, tool, action, resource, destination,
             payload_snapshot, payload_hash, reason, status, approver, created_at, decided_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                approval_id,
                request_id,
                agent_id,
                tool,
                action,
                resource,
                destination,
                json.dumps(payload_snapshot),
                payload_hash,
                reason,
                ApprovalDecision.PENDING.value,
                None,
                now_ts,
                None
            )
        )
        conn.commit()
    finally:
        conn.close()

    return ApprovalRecord(
        approval_id=approval_id,
        request_id=request_id,
        agent_id=agent_id,
        tool=tool,
        action=action,
        resource=resource,
        destination=destination,
        payload_snapshot=payload_snapshot,
        payload_hash=payload_hash,
        reason=reason,
        status=ApprovalDecision.PENDING.value,
        created_at=now_ts,
        decided_at=None,
        approver=None
    )


def get_approval(approval_id: str) -> Optional[ApprovalRecord]:
    """Retrieves an approval record by its ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, request_id, agent_id, tool, action, resource, destination,
                   payload_snapshot, payload_hash, reason, status, approver, created_at, decided_at
            FROM approvals
            WHERE id = ?;
            """,
            (approval_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        return ApprovalRecord(
            approval_id=d["id"],
            request_id=d["request_id"],
            agent_id=d["agent_id"],
            tool=d["tool"],
            action=d["action"],
            resource=d["resource"],
            destination=d["destination"],
            payload_snapshot=json.loads(d["payload_snapshot"]),
            payload_hash=d["payload_hash"],
            reason=d["reason"],
            status=d["status"],
            created_at=d["created_at"],
            decided_at=d["decided_at"],
            approver=d["approver"]
        )
    finally:
        conn.close()


def get_approvals(status_filter: Optional[str] = None) -> List[ApprovalRecord]:
    """Returns approvals optionally filtered by status."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if status_filter and status_filter.upper() != "ALL":
            cursor.execute(
                """
                SELECT id, request_id, agent_id, tool, action, resource, destination,
                       payload_snapshot, payload_hash, reason, status, approver, created_at, decided_at
                FROM approvals
                WHERE UPPER(status) = UPPER(?)
                ORDER BY created_at DESC;
                """,
                (status_filter,)
            )
        else:
            cursor.execute(
                """
                SELECT id, request_id, agent_id, tool, action, resource, destination,
                       payload_snapshot, payload_hash, reason, status, approver, created_at, decided_at
                FROM approvals
                ORDER BY created_at DESC;
                """
            )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            result.append(
                ApprovalRecord(
                    approval_id=d["id"],
                    request_id=d["request_id"],
                    agent_id=d["agent_id"],
                    tool=d["tool"],
                    action=d["action"],
                    resource=d["resource"],
                    destination=d["destination"],
                    payload_snapshot=json.loads(d["payload_snapshot"]),
                    payload_hash=d["payload_hash"],
                    reason=d["reason"],
                    status=d["status"],
                    created_at=d["created_at"],
                    decided_at=d["decided_at"],
                    approver=d["approver"]
                )
            )
        return result
    finally:
        conn.close()


def process_approval(
    approval_id: str,
    action: str,  # "APPROVE" or "REJECT"
    executor_callback: Optional[Callable[[Dict[str, Any]], Any]] = None,
    approver: str = "demo_human_approver"
) -> Tuple[bool, str, Optional[Any]]:
    """Processes an approval request atomically.
    
    Verifies PENDING state, enforces one-time use, validates SHA-256 hash binding.
    """
    approval = get_approval(approval_id)
    if not approval:
        return False, f"Approval ID '{approval_id}' not found.", None

    if approval.status != ApprovalDecision.PENDING.value:
        return (
            False,
            f"Approval '{approval_id}' is already {approval.status} and cannot be re-processed.",
            None
        )

    # Verify SHA-256 hash integrity of stored payload
    computed_hash = compute_payload_hash(approval.payload_snapshot)
    if computed_hash != approval.payload_hash:
        return (
            False,
            "Security Alert: Payload hash mismatch. Stored request data has been tampered with.",
            None
        )

    now_ts = datetime.now(timezone.utc).isoformat()
    conn = get_connection()

    if action == "REJECT":
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE approvals 
                SET status = ?, approver = ?, decided_at = ?
                WHERE id = ? AND status = ?;
                """,
                (ApprovalDecision.REJECTED.value, approver, now_ts, approval_id, ApprovalDecision.PENDING.value)
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Approval was modified concurrently or already resolved.", None
        finally:
            conn.close()

        # Audit the rejection
        record_audit_event(
            request_id=approval.request_id,
            agent_id=approval.agent_id,
            tool=approval.tool,
            action=approval.action,
            resource=approval.resource,
            destination=approval.destination,
            decision="REJECTED",
            reason_code="APPROVAL_REJECTED",
            reason=f"Human operator '{approver}' rejected the pending request.",
            execution_status="NOT_EXECUTED",
            approval_id=approval_id,
            timestamp=now_ts
        )

        return True, "Request successfully rejected by human operator. Zero tools executed.", None

    elif action == "APPROVE":
        # Atomically mark APPROVED before execution to prevent race condition replays
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE approvals 
                SET status = ?, approver = ?, decided_at = ?
                WHERE id = ? AND status = ?;
                """,
                (ApprovalDecision.APPROVED.value, approver, now_ts, approval_id, ApprovalDecision.PENDING.value)
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Approval was modified concurrently or already resolved.", None
        finally:
            conn.close()

        # Execute stored payload exactly once through executor callback
        result = None
        exec_status = "EXECUTED"
        if executor_callback:
            try:
                result = executor_callback(approval.payload_snapshot)
            except Exception as e:
                exec_status = "FAILED"
                result = {"error": f"Execution failed: {str(e)}"}

        # Audit the approval and execution
        record_audit_event(
            request_id=approval.request_id,
            agent_id=approval.agent_id,
            tool=approval.tool,
            action=approval.action,
            resource=approval.resource,
            destination=approval.destination,
            decision="APPROVED",
            reason_code="APPROVAL_GRANTED",
            reason=f"Human operator '{approver}' approved execution of the original payload snapshot.",
            execution_status=exec_status,
            approval_id=approval_id,
            timestamp=now_ts
        )

        return True, f"Request approved by human operator. Executed exact stored payload once ({exec_status}).", result

    return False, f"Unknown approval action '{action}'.", None
