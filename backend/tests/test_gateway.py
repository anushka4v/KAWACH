"""Unit and Integration tests for KAWACH Security Gateway enforcement.

Asserts on BOTH the decision and tool execution counts.
Proves that DENY and REQUIRE_APPROVAL never execute the underlying tool.
Tests fail-closed behavior, audit logging, and prompt injection defense.
"""

import os
import pytest
from app.database import init_db, clear_db
from app.gateway import handle_tool_request
from app.schemas import ToolRequest, DecisionType, ExecutionStatus, ReasonCode
from app.audit import get_audit_logs
from app.agent import run_agent_task
from data.seed_data import reset_state, get_current_state, tool_counters


@pytest.fixture(autouse=True)
def clean_test_environment(tmp_path):
    """Sets up an isolated SQLite database and fresh simulated state for each test."""
    test_db = str(tmp_path / "test_agentshield.db")
    os.environ["AGENTSHIELD_DB_PATH"] = test_db
    init_db(test_db)
    reset_state()
    yield
    clear_db(test_db)
    reset_state()


def test_allowed_action_executes_tool_once():
    """ALLOW decision executes the registered simulated tool exactly once."""
    initial_reads = tool_counters["document_reader.read"]
    req = ToolRequest(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="public_project_info.pdf"
    )
    resp = handle_tool_request(req)

    assert resp.decision == DecisionType.ALLOW.value
    assert resp.executed is True
    assert resp.execution_status == ExecutionStatus.EXECUTED.value
    assert resp.result is not None
    assert resp.result.get("success") is True
    assert "NovaTech Global Solutions" in resp.result.get("content", "")
    assert tool_counters["document_reader.read"] == initial_reads + 1


def test_denied_confidential_read_never_executes_tool():
    """DENY decision on confidential resource NEVER calls the tool (counter stays 0)."""
    initial_reads = tool_counters["document_reader.read"]
    req = ToolRequest(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="NovaTech_Financial_Report.pdf"
    )
    resp = handle_tool_request(req)

    assert resp.decision == DecisionType.DENY.value
    assert resp.executed is False
    assert resp.execution_status == ExecutionStatus.NOT_EXECUTED.value
    assert resp.result is None
    # Crucial proof: tool was NOT called
    assert tool_counters["document_reader.read"] == initial_reads


def test_denied_secret_read_never_executes_tool():
    """DENY decision on SECRET resource never calls the tool and returns no credential."""
    initial_reads = tool_counters["document_reader.read"]
    req = ToolRequest(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="api_credentials.txt"
    )
    resp = handle_tool_request(req)

    assert resp.decision == DecisionType.DENY.value
    assert resp.reason_code == ReasonCode.RESOURCE_SECRET.value
    assert resp.executed is False
    assert resp.result is None
    assert tool_counters["document_reader.read"] == initial_reads


def test_research_assistant_send_and_delete_denied_state_unchanged():
    """Research assistant attempting delete and send is DENIED with state completely unchanged."""
    initial_state = get_current_state()
    files_before = list(initial_state["simulated_files"])
    emails_before = len(initial_state["mock_sent_emails"])

    # 1. Attempt Delete
    del_req = ToolRequest(
        agent_id="research_assistant",
        tool="file_manager",
        action="delete",
        resource="NovaTech_Project_Report.pdf"
    )
    del_resp = handle_tool_request(del_req)
    assert del_resp.decision == DecisionType.DENY.value
    assert del_resp.executed is False

    # 2. Attempt Send Email
    send_req = ToolRequest(
        agent_id="research_assistant",
        tool="email_sender",
        action="send",
        resource="public_project_info.pdf",
        destination="teammate@example.com"
    )
    send_resp = handle_tool_request(send_req)
    assert send_resp.decision == DecisionType.DENY.value
    assert send_resp.executed is False

    # Verify state remains strictly untouched
    current_state = get_current_state()
    assert current_state["simulated_files"] == files_before
    assert len(current_state["mock_sent_emails"]) == emails_before
    assert current_state["tool_counters"]["file_manager.delete"] == 0
    assert current_state["tool_counters"]["email_sender.send"] == 0


def test_require_approval_does_not_execute_tool_on_creation():
    """REQUIRE_APPROVAL creates a pending approval record without executing the tool."""
    initial_sends = tool_counters["email_sender.send"]
    req = ToolRequest(
        agent_id="project_manager",
        tool="email_sender",
        action="send",
        resource="NovaTech_Financial_Report.pdf",
        destination="external-auditor@example.com",
        arguments={"subject": "Q3 Audit Package"}
    )
    resp = handle_tool_request(req)

    assert resp.decision == DecisionType.REQUIRE_APPROVAL.value
    assert resp.reason_code == ReasonCode.APPROVAL_REQUIRED.value
    assert resp.executed is False
    assert resp.execution_status == ExecutionStatus.PENDING_APPROVAL.value
    assert resp.approval_id is not None
    # Crucial proof: send counter remained 0
    assert tool_counters["email_sender.send"] == initial_sends
    assert len(get_current_state()["mock_sent_emails"]) == 0


def test_unknown_tool_fails_closed():
    """Unknown tool name returns DENY and executes zero tools."""
    req = ToolRequest(
        agent_id="research_assistant",
        tool="malicious_shell_runner",
        action="run",
        resource=None
    )
    resp = handle_tool_request(req)
    assert resp.decision == DecisionType.DENY.value
    assert resp.reason_code == ReasonCode.UNKNOWN_TOOL.value
    assert resp.executed is False
    assert resp.execution_status == ExecutionStatus.NOT_EXECUTED.value


def test_unknown_resource_fails_closed():
    """Unknown resource returns DENY and zero tool executions."""
    req = ToolRequest(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="unknown_unregistered_file.pdf"
    )
    resp = handle_tool_request(req)
    assert resp.decision == DecisionType.DENY.value
    assert resp.reason_code == ReasonCode.UNKNOWN_RESOURCE.value
    assert resp.executed is False


def test_simulated_policy_exception_fails_closed():
    """Simulated policy exception returns DENY with POLICY_ERROR without crashing server."""
    req = ToolRequest(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="public_project_info.pdf",
        arguments={"trigger_test_policy_crash": True}
    )
    resp = handle_tool_request(req)
    assert resp.decision == DecisionType.DENY.value
    assert resp.reason_code == ReasonCode.POLICY_ERROR.value
    assert resp.executed is False
    assert resp.execution_status == ExecutionStatus.NOT_EXECUTED.value


def test_prompt_injection_scenario_blocks_unauthorized_actions():
    """Demo 2 EchoLeak-inspired scenario: malicious instructions produce DENY decisions and zero exfiltration."""
    task_resp = run_agent_task(
        task="Summarise this incoming project email.",
        agent_id="research_assistant",
        scenario_id=2
    )
    assert len(task_resp.results) == 3

    # Step 1: Read fixture (allowed as untrusted data)
    step1 = task_resp.results[0]
    assert step1.decision == DecisionType.ALLOW.value
    assert step1.executed is True
    assert "Assistant: ignore previous instructions" in step1.result["content"]

    # Step 2: Read api_credentials.txt (DENIED)
    step2 = task_resp.results[1]
    assert step2.decision == DecisionType.DENY.value
    assert step2.reason_code == ReasonCode.RESOURCE_SECRET.value
    assert step2.executed is False
    assert step2.result is None

    # Step 3: Send email to attacker (DENIED)
    step3 = task_resp.results[2]
    assert step3.decision == DecisionType.DENY.value
    assert step3.executed is False

    # Verify zero secrets leaked and zero emails sent
    state = get_current_state()
    assert len(state["mock_sent_emails"]) == 0
    assert state["tool_counters"]["email_sender.send"] == 0


def test_audit_logs_recorded_for_all_requests():
    """Audit records are created for all decisions with appropriate execution status."""
    req1 = ToolRequest(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="public_project_info.pdf"
    )
    handle_tool_request(req1)

    req2 = ToolRequest(
        agent_id="research_assistant",
        tool="document_reader",
        action="read",
        resource="api_credentials.txt"
    )
    handle_tool_request(req2)

    logs = get_audit_logs()
    assert len(logs) >= 2
    # Check that decisions and execution_status are recorded accurately
    statuses = {log["execution_status"] for log in logs}
    assert ExecutionStatus.EXECUTED.value in statuses
    assert ExecutionStatus.NOT_EXECUTED.value in statuses
