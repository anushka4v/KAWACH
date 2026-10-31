"""Unit tests for pure deterministic policy evaluation in KAWACH / AGENTSHIELD.

Verifies role-based access rules, sensitivity levels, boundary conditions,
and fail-closed invariants without executing any tools.
"""

import pytest
from app.policy import evaluate_policy, is_external_destination
from app.schemas import DecisionType, ReasonCode


def test_research_assistant_public_read_allowed():
    """Research assistant may read registered PUBLIC documents."""
    decision, code, reason = evaluate_policy(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="public_project_info.pdf"
    )
    assert decision == DecisionType.ALLOW
    assert code == ReasonCode.PERMISSION_GRANTED
    assert "granted" in reason.lower() or "permitted" in reason.lower()


def test_research_assistant_confidential_read_denied():
    """Research assistant must be denied access to CONFIDENTIAL resources."""
    decision, code, reason = evaluate_policy(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="NovaTech_Financial_Report.pdf"
    )
    assert decision == DecisionType.DENY
    assert code == ReasonCode.RESOURCE_CONFIDENTIAL


def test_research_assistant_secret_read_denied():
    """Access to SECRET resource is strictly denied to Research Assistant."""
    decision, code, reason = evaluate_policy(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="api_credentials.txt"
    )
    assert decision == DecisionType.DENY
    assert code == ReasonCode.RESOURCE_SECRET


def test_research_assistant_file_deletion_denied():
    """Research assistant must be denied file deletion."""
    decision, code, reason = evaluate_policy(
        agent_id="research_assistant",
        tool="file_manager",
        action="delete",
        resource="NovaTech_Project_Report.pdf"
    )
    assert decision == DecisionType.DENY
    assert code == ReasonCode.ACTION_NOT_ALLOWED


def test_research_assistant_email_send_denied():
    """Research assistant must be denied email transmission."""
    decision, code, reason = evaluate_policy(
        agent_id="research_assistant",
        tool="email_sender",
        action="send",
        resource="public_project_info.pdf",
        destination="teammate@example.com"
    )
    assert decision == DecisionType.DENY
    assert code == ReasonCode.TOOL_NOT_ALLOWED


def test_research_assistant_file_listing_allowed():
    """Research assistant is permitted to list directory files."""
    decision, code, reason = evaluate_policy(
        agent_id="research_assistant",
        tool="file_manager",
        action="list"
    )
    assert decision == DecisionType.ALLOW
    assert code == ReasonCode.PERMISSION_GRANTED


def test_project_manager_internal_read_allowed():
    """Project manager is permitted to read INTERNAL documents."""
    decision, code, reason = evaluate_policy(
        agent_id="project_manager",
        tool="document_reader",
        action="read",
        resource="NovaTech_Project_Report.pdf"
    )
    assert decision == DecisionType.ALLOW
    assert code == ReasonCode.PERMISSION_GRANTED


def test_project_manager_secret_read_denied():
    """Project manager is denied access to SECRET resources."""
    decision, code, reason = evaluate_policy(
        agent_id="project_manager",
        tool="document_reader",
        action="read",
        resource="api_credentials.txt"
    )
    assert decision == DecisionType.DENY
    assert code == ReasonCode.RESOURCE_SECRET


def test_project_manager_confidential_external_send_requires_approval():
    """Project manager sending CONFIDENTIAL resource to external recipient requires approval."""
    decision, code, reason = evaluate_policy(
        agent_id="project_manager",
        tool="email_sender",
        action="send",
        resource="NovaTech_Financial_Report.pdf",
        destination="external-auditor@example.com"
    )
    assert decision == DecisionType.REQUIRE_APPROVAL
    assert code == ReasonCode.APPROVAL_REQUIRED


def test_project_manager_draft_email_allowed():
    """Project manager is permitted to draft emails."""
    decision, code, reason = evaluate_policy(
        agent_id="project_manager",
        tool="email_sender",
        action="draft",
        resource="public_project_info.pdf",
        destination="team@novatech.internal"
    )
    assert decision == DecisionType.ALLOW
    assert code == ReasonCode.PERMISSION_GRANTED


def test_unknown_agent_fails_closed():
    """Unknown agent identity results in DENY with UNKNOWN_AGENT code."""
    decision, code, reason = evaluate_policy(
        agent_id="rogue_agent_99",
        tool="document_reader",
        action="read",
        resource="public_project_info.pdf"
    )
    assert decision == DecisionType.DENY
    assert code == ReasonCode.UNKNOWN_AGENT


def test_unknown_tool_fails_closed():
    """Unknown tool name results in DENY with UNKNOWN_TOOL code."""
    decision, code, reason = evaluate_policy(
        agent_id="research_assistant",
        tool="terminal_shell",
        action="execute",
        resource="script.sh"
    )
    assert decision == DecisionType.DENY
    assert code == ReasonCode.UNKNOWN_TOOL


def test_unknown_resource_fails_closed():
    """Unregistered resource name results in DENY with UNKNOWN_RESOURCE code."""
    decision, code, reason = evaluate_policy(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="non_existent_confidential_file.pdf"
    )
    assert decision == DecisionType.DENY
    assert code == ReasonCode.UNKNOWN_RESOURCE


def test_path_traversal_resource_rejected():
    """Path traversal attempt in resource parameter is rejected."""
    decision, code, reason = evaluate_policy(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="../../etc/passwd"
    )
    assert decision == DecisionType.DENY
    assert code == ReasonCode.UNKNOWN_RESOURCE


def test_external_destination_detection():
    """Verifies internal vs external destination detection."""
    assert is_external_destination("external-auditor@example.com") is True
    assert is_external_destination("attacker@example.com") is True
    assert is_external_destination("alice@novatech.internal") is False
    assert is_external_destination(None) is False
