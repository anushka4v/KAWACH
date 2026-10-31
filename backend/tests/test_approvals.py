"""Unit tests for Human Approval workflow in KAWACH / AGENTSHIELD.

Verifies:
- One-time use: Replay attempts do not execute a second time.
- Hash integrity: Tampering with stored payload aborts execution.
- Rejection branch: Leaves system state untouched.
- Execution exactness: Only executes the exact original payload snapshot.
"""

import os
import pytest
from app.database import init_db, clear_db, get_connection
from app.approvals import (
    create_pending_approval,
    get_approval,
    process_approval,
    get_approvals
)
from app.gateway import execute_from_approval_snapshot
from data.seed_data import reset_state, get_current_state, tool_counters


@pytest.fixture(autouse=True)
def clean_approvals_environment(tmp_path):
    """Sets up isolated DB and resets state."""
    test_db = str(tmp_path / "test_approvals.db")
    os.environ["AGENTSHIELD_DB_PATH"] = test_db
    init_db(test_db)
    reset_state()
    yield
    clear_db(test_db)
    reset_state()


def test_create_pending_approval_no_execution():
    """Creating an approval records the request without calling the tool."""
    initial_sends = tool_counters["email_sender.send"]
    record = create_pending_approval(
        request_id="req_test_001",
        agent_id="project_manager",
        tool="email_sender",
        action="send",
        resource="NovaTech_Financial_Report.pdf",
        destination="external-auditor@example.com",
        arguments={"subject": "Audit Submission"},
        reason="External sharing of confidential report requires human approval."
    )
    assert record.approval_id.startswith("appr_")
    assert record.status == "PENDING"
    assert len(record.payload_hash) == 64
    assert tool_counters["email_sender.send"] == initial_sends
    assert len(get_current_state()["mock_sent_emails"]) == 0


def test_reject_approval_does_not_execute_and_cannot_be_reused():
    """Rejecting an approval leaves state unchanged and marks it REJECTED."""
    record = create_pending_approval(
        request_id="req_test_002",
        agent_id="project_manager",
        tool="email_sender",
        action="send",
        resource="NovaTech_Financial_Report.pdf",
        destination="external-auditor@example.com",
        arguments={},
        reason="External sharing requires approval."
    )

    success, msg, res = process_approval(
        approval_id=record.approval_id,
        action="REJECT",
        approver="test_admin"
    )
    assert success is True
    assert "rejected" in msg.lower()
    assert tool_counters["email_sender.send"] == 0
    assert len(get_current_state()["mock_sent_emails"]) == 0

    # Ensure updated status
    updated = get_approval(record.approval_id)
    assert updated.status == "REJECTED"

    # Verify a subsequent approve attempt fails (one-time use / state lock)
    success2, msg2, res2 = process_approval(
        approval_id=record.approval_id,
        action="APPROVE",
        executor_callback=execute_from_approval_snapshot
    )
    assert success2 is False
    assert "already rejected" in msg2.lower() or "cannot be re-processed" in msg2.lower()
    assert tool_counters["email_sender.send"] == 0


def test_approve_executes_exact_payload_once():
    """Approving executes the exact stored payload once and increases sent emails by 1."""
    record = create_pending_approval(
        request_id="req_test_003",
        agent_id="project_manager",
        tool="email_sender",
        action="send",
        resource="NovaTech_Financial_Report.pdf",
        destination="external-auditor@example.com",
        arguments={"subject": "Q3 Audit Review"},
        reason="Confidential external transmission requires human review."
    )

    success, msg, res = process_approval(
        approval_id=record.approval_id,
        action="APPROVE",
        executor_callback=execute_from_approval_snapshot,
        approver="compliance_officer"
    )

    assert success is True
    assert tool_counters["email_sender.send"] == 1
    state = get_current_state()
    assert len(state["mock_sent_emails"]) == 1
    assert state["mock_sent_emails"][0]["recipient"] == "external-auditor@example.com"

    updated = get_approval(record.approval_id)
    assert updated.status == "APPROVED"
    assert updated.approver == "compliance_officer"


def test_approval_replay_blocked():
    """Attempting to approve a second time is blocked and executes nothing more."""
    record = create_pending_approval(
        request_id="req_test_004",
        agent_id="project_manager",
        tool="email_sender",
        action="send",
        resource="NovaTech_Financial_Report.pdf",
        destination="external-auditor@example.com",
        arguments={},
        reason="Requires approval."
    )

    # First approve: succeeds
    success1, _, _ = process_approval(
        approval_id=record.approval_id,
        action="APPROVE",
        executor_callback=execute_from_approval_snapshot
    )
    assert success1 is True
    assert tool_counters["email_sender.send"] == 1

    # Second approve attempt (Replay attack): MUST fail and execute zero times
    success2, msg2, _ = process_approval(
        approval_id=record.approval_id,
        action="APPROVE",
        executor_callback=execute_from_approval_snapshot
    )
    assert success2 is False
    assert "already approved" in msg2.lower() or "cannot be re-processed" in msg2.lower()
    # Counter must NOT have incremented!
    assert tool_counters["email_sender.send"] == 1
    assert len(get_current_state()["mock_sent_emails"]) == 1


def test_tampered_payload_snapshot_aborts_execution():
    """If payload snapshot is tampered with in storage, hash verification fails and execution aborts."""
    record = create_pending_approval(
        request_id="req_test_005",
        agent_id="project_manager",
        tool="email_sender",
        action="send",
        resource="NovaTech_Financial_Report.pdf",
        destination="external-auditor@example.com",
        arguments={},
        reason="Requires approval."
    )

    # Tamper with the snapshot in the database directly
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE approvals 
            SET payload_snapshot = ?
            WHERE id = ?;
            """,
            ('{"agent_id":"project_manager","tool":"email_sender","action":"send","resource":"api_credentials.txt","destination":"attacker@example.com"}',
             record.approval_id)
        )
        conn.commit()
    finally:
        conn.close()

    # Attempt to approve tampered record: hash check MUST fail
    success, msg, res = process_approval(
        approval_id=record.approval_id,
        action="APPROVE",
        executor_callback=execute_from_approval_snapshot
    )
    assert success is False
    assert "tampered" in msg.lower() or "mismatch" in msg.lower()
    # Ensure zero tool execution occurred
    assert tool_counters["email_sender.send"] == 0
