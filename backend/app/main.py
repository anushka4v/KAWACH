"""FastAPI Main Application for KAWACH (AGENTSHIELD).

AI Agent Security Gateway.
Exposes standard REST endpoints for task submission, gateway enforcement,
approval workflows, audit inspection, and simulated state management.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, clear_db
from app.schemas import (
    TaskSubmitRequest,
    TaskSubmitResponse,
    ApprovalRecord,
    ApprovalActionResponse,
    AuditLogRecord,
    ResetResponse
)
from app.audit import get_audit_logs, get_requests
from app.approvals import get_approvals, process_approval
from app.agent import run_agent_task
from app.gateway import execute_from_approval_snapshot
from data.seed_data import get_current_state, reset_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialises SQLite database schema on startup."""
    init_db()
    yield


app = FastAPI(
    title="KAWACH - AI Agent Security Gateway",
    description="Deterministic runtime policy enforcement and audit gateway for AI agents.",
    version="1.0.0",
    lifespan=lifespan
)

DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def get_allowed_origins() -> List[str]:
    """Parse comma-separated ALLOWED_ORIGINS, defaulting to local dev origins.

    A wildcard is never allowed because credentials are enabled.
    """
    raw = os.environ.get("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    origins = [origin for origin in origins if origin != "*"]
    return origins or DEFAULT_ALLOWED_ORIGINS.split(",")


# CORS: configurable via ALLOWED_ORIGINS (comma-separated).
# Never use "*" together with credentials.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
   allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint to verify backend status."""
    return {"status": "ok"}


@app.post("/api/tasks", response_model=TaskSubmitResponse)
async def submit_task(payload: TaskSubmitRequest) -> TaskSubmitResponse:
    """Submits a user task or demo scenario to the agent and gateway."""
    try:
        response = run_agent_task(
            task=payload.task,
            agent_id=payload.agent_id,
            scenario_id=payload.scenario_id,
            case=payload.case
        )
        return response
    except Exception as e:
        # Never leak internal stack trace
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while evaluating the task through the security gateway."
        )


@app.get("/api/requests")
async def list_requests(limit: int = Query(default=100, ge=1, le=500)) -> List[Dict[str, Any]]:
    """Returns request history with tool, action, resource, decision, and reason."""
    try:
        return get_requests(limit=limit)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve request history."
        )


@app.get("/api/approvals", response_model=List[ApprovalRecord])
async def list_approvals(
    status_filter: Optional[str] = Query(default="PENDING", alias="status")
) -> List[ApprovalRecord]:
    """Returns pending human approvals (or filtered by status)."""
    try:
        return get_approvals(status_filter=status_filter)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve approval records."
        )


@app.post("/api/approvals/{approval_id}/approve", response_model=ApprovalActionResponse)
async def approve_request(approval_id: str) -> ApprovalActionResponse:
    """Approves a pending action. Enforces one-time execution of the exact stored payload snapshot."""
    try:
        success, message, result = process_approval(
            approval_id=approval_id,
            action="APPROVE",
            executor_callback=execute_from_approval_snapshot,
            approver="demo_human_approver"
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        return ApprovalActionResponse(
            approval_id=approval_id,
            status="APPROVED",
            message=message,
            executed=True,
            result=result
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while processing approval."
        )


@app.post("/api/approvals/{approval_id}/reject", response_model=ApprovalActionResponse)
async def reject_request(approval_id: str) -> ApprovalActionResponse:
    """Rejects a pending action. Leaves system state unchanged and records rejection."""
    try:
        success, message, _ = process_approval(
            approval_id=approval_id,
            action="REJECT",
            approver="demo_human_approver"
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        return ApprovalActionResponse(
            approval_id=approval_id,
            status="REJECTED",
            message=message,
            executed=False,
            result=None
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while processing rejection."
        )


@app.get("/api/audit-logs", response_model=List[AuditLogRecord])
async def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    decision: Optional[str] = Query(default=None)
) -> List[AuditLogRecord]:
    """Returns chronological audit records of security decisions and execution evidence."""
    try:
        logs = get_audit_logs(limit=limit, decision_filter=decision)
        return [AuditLogRecord(**log) for log in logs]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit log records."
        )


@app.get("/api/state")
async def get_state() -> Dict[str, Any]:
    """Inspection endpoint for demo evidence: returns simulated files, mock sent emails, and tool counters."""
    return get_current_state()


@app.post("/api/demo/reset", response_model=ResetResponse)
async def reset_demo() -> ResetResponse:
    """Restores clean demo state: clears emails, approvals, audit logs, and simulated file store."""
    try:
        # Clear SQLite tables
        clear_db()
        # Reset in-memory simulated tools state
        clean_state = reset_state()
        return ResetResponse(
            status="ok",
            message="Clean demo state restored. In-memory tools and database logs reset.",
            state=clean_state
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset demo state."
        )
