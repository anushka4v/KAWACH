"""Full end-to-end API integration tests for KAWACH FastAPI endpoints.

Tests every REST endpoint with httpx / starlette TestClient, verifying:
- Health check
- Task submissions across all six demo scenarios
- Request history and audit logging
- Human approval queue, approve, and reject endpoints
- State inspection and demo reset
"""

import os
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.database import init_db, clear_db
from data.seed_data import reset_state


@pytest.fixture(autouse=True)
def setup_api_test_env(tmp_path):
    test_db = str(tmp_path / "test_api.db")
    os.environ["AGENTSHIELD_DB_PATH"] = test_db
    init_db(test_db)
    reset_state()
    yield
    clear_db(test_db)
    reset_state()


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    """GET /api/health returns {'status': 'ok'}."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_demo_1_legitimate(client):
    """Demo 1: Legitimate task execution."""
    resp = client.post("/api/tasks", json={
        "task": "Read public_project_info.pdf and summarise the project objectives. Then list the available demo files.",
        "agent_id": "research_assistant",
        "scenario_id": 1
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary_decision"] == "ALLOW"
    assert len(data["results"]) == 2
    assert all(r["decision"] == "ALLOW" for r in data["results"])
    assert all(r["executed"] is True for r in data["results"])


def test_api_demo_2_prompt_injection(client):
    """Demo 2: EchoLeak-inspired prompt injection simulation."""
    resp = client.post("/api/tasks", json={
        "task": "Summarise this incoming project email.",
        "agent_id": "research_assistant",
        "scenario_id": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    # 3 results: step 1 ALLOW, step 2 DENY (SECRET), step 3 DENY (TOOL_NOT_ALLOWED)
    assert len(data["results"]) == 3
    assert data["results"][0]["decision"] == "ALLOW"
    assert data["results"][1]["decision"] == "DENY"
    assert data["results"][1]["reason_code"] == "RESOURCE_SECRET"
    assert data["results"][2]["decision"] == "DENY"
    # No credentials in any result
    assert "DEMO_KEY_NOT_VALID" not in str(data)


def test_api_demo_3_sensitive_data(client):
    """Demo 3: Sensitive-data access attempt."""
    resp = client.post("/api/tasks", json={
        "task": "Read all corporate files.",
        "agent_id": "research_assistant",
        "scenario_id": 3
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 4
    assert data["results"][0]["decision"] == "ALLOW"
    assert data["results"][1]["decision"] == "DENY"
    assert data["results"][2]["decision"] == "DENY"
    assert data["results"][3]["decision"] == "DENY"


def test_api_demo_4_tool_permission(client):
    """Demo 4: Tool permission violation."""
    resp = client.post("/api/tasks", json={
        "task": "List files, delete report, send email.",
        "agent_id": "research_assistant",
        "scenario_id": 4
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 3
    assert data["results"][0]["decision"] == "ALLOW"
    assert data["results"][1]["decision"] == "DENY"
    assert data["results"][2]["decision"] == "DENY"


def test_api_demo_5_approval_workflow_reject_and_approve(client):
    """Demo 5: Human approval workflow test through API endpoints."""
    # 1. Submit approval scenario
    task_resp = client.post("/api/tasks", json={
        "task": "Prepare to share NovaTech_Financial_Report.pdf with external-auditor@example.com.",
        "agent_id": "project_manager",
        "scenario_id": 5
    })
    assert task_resp.status_code == 200
    data = task_resp.json()
    assert data["summary_decision"] == "REQUIRE_APPROVAL"
    result_action = data["results"][0]
    assert result_action["decision"] == "REQUIRE_APPROVAL"
    approval_id = result_action["approval_id"]
    assert approval_id is not None

    # Check pending approvals endpoint
    appr_resp = client.get("/api/approvals?status=PENDING")
    assert appr_resp.status_code == 200
    pending_list = appr_resp.json()
    assert any(a["approval_id"] == approval_id for a in pending_list)

    # 2. Test Reject Branch on this approval
    rej_resp = client.post(f"/api/approvals/{approval_id}/reject")
    assert rej_resp.status_code == 200
    rej_data = rej_resp.json()
    assert rej_data["status"] == "REJECTED"
    assert rej_data["executed"] is False

    # Check state: zero emails sent
    state_resp = client.get("/api/state")
    assert len(state_resp.json()["mock_sent_emails"]) == 0

    # 3. Create fresh approval for Approve branch
    task_resp2 = client.post("/api/tasks", json={
        "task": "Prepare to share NovaTech_Financial_Report.pdf with external-auditor@example.com.",
        "agent_id": "project_manager",
        "scenario_id": 5
    })
    approval_id2 = task_resp2.json()["results"][0]["approval_id"]

    # Approve second request
    appr_action_resp = client.post(f"/api/approvals/{approval_id2}/approve")
    assert appr_action_resp.status_code == 200
    appr_action_data = appr_action_resp.json()
    assert appr_action_data["status"] == "APPROVED"
    assert appr_action_data["executed"] is True

    # Check state: exactly one email sent
    state_resp2 = client.get("/api/state")
    assert len(state_resp2.json()["mock_sent_emails"]) == 1

    # Replay attempt on approved approval: MUST return error 400
    replay_resp = client.post(f"/api/approvals/{approval_id2}/approve")
    assert replay_resp.status_code == 400
    assert "already approved" in replay_resp.json()["detail"].lower()

    # Replay attempt on rejected approval: MUST return error 400
    replay_rej = client.post(f"/api/approvals/{approval_id}/reject")
    assert replay_rej.status_code == 400


def test_api_demo_6_fail_closed_subcases(client):
    """Demo 6: Fail-closed behaviour across all subcases."""
    for case in [1, 2, 3, 4, 5]:
        resp = client.post("/api/tasks", json={
            "task": f"Fail closed test case {case}",
            "agent_id": "research_assistant",
            "scenario_id": 6,
            "case": case
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary_decision"] == "DENY"
        assert all(r["decision"] == "DENY" for r in data["results"])
        assert all(r["executed"] is False for r in data["results"])


def test_api_reset_endpoint(client):
    """POST /api/demo/reset restores clean demo state."""
    # First submit some actions
    client.post("/api/tasks", json={
        "task": "Read public_project_info.pdf",
        "agent_id": "research_assistant",
        "scenario_id": 1
    })

    # Call reset
    reset_resp = client.post("/api/demo/reset")
    assert reset_resp.status_code == 200
    data = reset_resp.json()
    assert data["status"] == "ok"

    # Verify state is clean
    audit_resp = client.get("/api/audit-logs")
    assert len(audit_resp.json()) == 0

    state_resp = client.get("/api/state")
    state = state_resp.json()
    assert len(state["mock_sent_emails"]) == 0
    assert state["tool_counters"]["document_reader.read"] == 0
