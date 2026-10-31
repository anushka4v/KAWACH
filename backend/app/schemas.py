"""Pydantic schemas and strict request/response data contracts for KAWACH.

Enforces strict schema validation (extra='forbid').
Never allows malformed or unexpected fields to bypass the gateway.
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, ConfigDict, Field


class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class ExecutionStatus(str, Enum):
    NOT_EXECUTED = "NOT_EXECUTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    PENDING_APPROVAL = "PENDING_APPROVAL"


class ReasonCode(str, Enum):
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    TOOL_NOT_ALLOWED = "TOOL_NOT_ALLOWED"
    ACTION_NOT_ALLOWED = "ACTION_NOT_ALLOWED"
    RESOURCE_CONFIDENTIAL = "RESOURCE_CONFIDENTIAL"
    RESOURCE_SECRET = "RESOURCE_SECRET"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    UNKNOWN_AGENT = "UNKNOWN_AGENT"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"
    UNKNOWN_RESOURCE = "UNKNOWN_RESOURCE"
    INVALID_REQUEST = "INVALID_REQUEST"
    POLICY_ERROR = "POLICY_ERROR"


class ToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: Optional[str] = None
    agent_id: str
    tool: str
    action: str
    resource: Optional[str] = None
    destination: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)


class GatewayResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    agent_id: str
    tool: str
    action: str
    resource: Optional[str] = None
    destination: Optional[str] = None
    decision: str
    reason_code: str
    reason: str
    executed: bool
    execution_status: str
    result: Optional[Any] = None
    approval_id: Optional[str] = None


class TaskSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: str
    agent_id: str
    scenario_id: Optional[int] = None
    case: Optional[Union[str, int]] = None


class TaskSubmitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    agent_id: str
    task: str
    status: str
    summary_decision: str
    results: List[GatewayResponse]


class ApprovalDecision(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    request_id: str
    agent_id: str
    tool: str
    action: str
    resource: Optional[str] = None
    destination: Optional[str] = None
    payload_snapshot: Dict[str, Any]
    payload_hash: str
    reason: str
    status: str
    created_at: str
    decided_at: Optional[str] = None
    approver: Optional[str] = None


class ApprovalActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    status: str
    message: str
    executed: bool
    result: Optional[Any] = None


class AuditLogRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    request_id: str
    agent_id: str
    tool: str
    action: str
    resource: Optional[str] = None
    destination: Optional[str] = None
    decision: str
    reason_code: str
    reason: str
    execution_status: str
    approval_id: Optional[str] = None
    timestamp: str


class ResetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    message: str
    state: Dict[str, Any]
