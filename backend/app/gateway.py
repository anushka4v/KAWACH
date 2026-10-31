"""Security Gateway Enforcement Point for KAWACH / AGENTSHIELD.

Single authoritative enforcement point: every proposed tool action MUST pass
through handle_tool_request().

Core Safety Invariant:
No direct code path exists from the agent to any tool.
DENY and REQUIRE_APPROVAL never execute the underlying tool function.
Unknown tools, missing fields, and internal policy exceptions FAIL CLOSED.
"""

import os
import uuid
from typing import Optional, Dict, Any, Callable
from app.schemas import (
    ToolRequest,
    GatewayResponse,
    DecisionType,
    ExecutionStatus,
    ReasonCode
)
from app.policy import evaluate_policy
from app.audit import record_request, record_audit_event
from app.approvals import create_pending_approval
from app.tools import document_reader, file_manager, email_sender

# Canonical simulated tool registry
DEFAULT_TOOL_REGISTRY: Dict[str, Dict[str, Callable[[ToolRequest], Any]]] = {
    "document_reader": {
        "read": lambda req: document_reader.read(req.resource or "")
    },
    "file_manager": {
        "list": lambda req: file_manager.list_files(),
        "delete": lambda req: file_manager.delete_file(req.resource or "")
    },
    "email_sender": {
        "send": lambda req: email_sender.send_email(
            recipient=req.destination or req.arguments.get("recipient", "unknown@novatech.internal"),
            subject=req.arguments.get("subject", f"Document Transmission: {req.resource or 'Notification'}"),
            body=req.arguments.get("body", f"Transmitted content for resource '{req.resource or 'data'}'.")
        ),
        "draft": lambda req: email_sender.draft_email(
            recipient=req.destination or req.arguments.get("recipient", "draft@novatech.internal"),
            subject=req.arguments.get("subject", f"Draft: {req.resource or 'Task'}"),
            body=req.arguments.get("body", f"Draft body for '{req.resource or 'task'}'.")
        )
    }
}


def execute_registered_tool(
    request: ToolRequest,
    registry: Optional[Dict[str, Dict[str, Callable]]] = None
) -> Any:
    """Executes a registered simulated tool. Only called when decision is ALLOW or APPROVED."""
    reg = registry or DEFAULT_TOOL_REGISTRY
    tool_entry = reg.get(request.tool, {})
    handler = tool_entry.get(request.action)
    if not handler:
        raise ValueError(f"No executable handler registered for {request.tool}.{request.action}")
    return handler(request)


def execute_from_approval_snapshot(
    payload: Dict[str, Any],
    registry: Optional[Dict[str, Dict[str, Callable]]] = None
) -> Any:
    """Reconstructs a ToolRequest from immutable approval snapshot and executes it once."""
    req = ToolRequest(
        request_id=payload.get("request_id"),
        agent_id=payload.get("agent_id", "unknown"),
        tool=payload.get("tool", "unknown"),
        action=payload.get("action", "unknown"),
        resource=payload.get("resource"),
        destination=payload.get("destination"),
        arguments=payload.get("arguments", {})
    )
    return execute_registered_tool(req, registry)


def handle_tool_request(
    request: ToolRequest,
    tool_registry: Optional[Dict[str, Dict[str, Callable]]] = None
) -> GatewayResponse:
    """Authoritative gateway entry point. Enforces security boundary for all tool actions."""
    reg = tool_registry or DEFAULT_TOOL_REGISTRY

    # Ensure unique request ID
    if not request.request_id:
        request.request_id = f"req_{uuid.uuid4().hex[:10]}"

    # 1. Log incoming request in requests table
    try:
        record_request(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            arguments=request.arguments
        )
    except Exception:
        # Non-blocking for request recording error
        pass

    # 2. Check tool existence in tool registry
    if request.tool not in reg or request.action not in reg[request.tool]:
        record_audit_event(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=DecisionType.DENY.value,
            reason_code=ReasonCode.UNKNOWN_TOOL.value,
            reason=f"Tool or action '{request.tool}.{request.action}' is not in the authorized tool registry.",
            execution_status=ExecutionStatus.NOT_EXECUTED.value
        )
        return GatewayResponse(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=DecisionType.DENY.value,
            reason_code=ReasonCode.UNKNOWN_TOOL.value,
            reason=f"Tool or action '{request.tool}.{request.action}' is not in the authorized tool registry.",
            executed=False,
            execution_status=ExecutionStatus.NOT_EXECUTED.value,
            result=None,
            approval_id=None
        )

    # 3. Policy failure simulation hook (for Demo 6 test case)
    # Controlled strictly via KAWACH_TEST_MODE or request argument
    test_mode = os.environ.get("KAWACH_TEST_MODE", "0") == "1"
    if (test_mode and request.arguments.get("simulate_policy_error")) or request.arguments.get("trigger_test_policy_crash"):
        record_audit_event(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=DecisionType.DENY.value,
            reason_code=ReasonCode.POLICY_ERROR.value,
            reason="Internal policy evaluation failure encountered. Gate failed closed safely.",
            execution_status=ExecutionStatus.NOT_EXECUTED.value
        )
        return GatewayResponse(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=DecisionType.DENY.value,
            reason_code=ReasonCode.POLICY_ERROR.value,
            reason="Internal policy evaluation failure encountered. Gate failed closed safely.",
            executed=False,
            execution_status=ExecutionStatus.NOT_EXECUTED.value,
            result=None,
            approval_id=None
        )

    # 4. Evaluate deterministic policy inside try/except to fail closed on any unexpected exception
    try:
        decision, reason_code, reason = evaluate_policy(
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            arguments=request.arguments
        )
    except Exception as e:
        # Fail closed on any unhandled policy exception - NEVER expose stack trace
        record_audit_event(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=DecisionType.DENY.value,
            reason_code=ReasonCode.POLICY_ERROR.value,
            reason="Unexpected policy engine exception. Security gateway failed closed safely.",
            execution_status=ExecutionStatus.NOT_EXECUTED.value
        )
        return GatewayResponse(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=DecisionType.DENY.value,
            reason_code=ReasonCode.POLICY_ERROR.value,
            reason="Unexpected policy engine exception. Security gateway failed closed safely.",
            executed=False,
            execution_status=ExecutionStatus.NOT_EXECUTED.value,
            result=None,
            approval_id=None
        )

    # 5. Handle DENY: tool must NEVER run
    if decision == DecisionType.DENY:
        record_audit_event(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=decision.value,
            reason_code=reason_code.value,
            reason=reason,
            execution_status=ExecutionStatus.NOT_EXECUTED.value
        )
        return GatewayResponse(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=decision.value,
            reason_code=reason_code.value,
            reason=reason,
            executed=False,
            execution_status=ExecutionStatus.NOT_EXECUTED.value,
            result=None,
            approval_id=None
        )

    # 6. Handle REQUIRE_APPROVAL: pause action, store immutable snapshot, do NOT execute
    if decision == DecisionType.REQUIRE_APPROVAL:
        appr_record = create_pending_approval(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            arguments=request.arguments,
            reason=reason
        )
        record_audit_event(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=decision.value,
            reason_code=reason_code.value,
            reason=reason,
            execution_status=ExecutionStatus.PENDING_APPROVAL.value,
            approval_id=appr_record.approval_id
        )
        return GatewayResponse(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=decision.value,
            reason_code=reason_code.value,
            reason=reason,
            executed=False,
            execution_status=ExecutionStatus.PENDING_APPROVAL.value,
            result=None,
            approval_id=appr_record.approval_id
        )

    # 7. Handle ALLOW: execute simulated tool through registered handler
    try:
        tool_result = execute_registered_tool(request, reg)
        record_audit_event(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=decision.value,
            reason_code=reason_code.value,
            reason=reason,
            execution_status=ExecutionStatus.EXECUTED.value
        )
        return GatewayResponse(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=decision.value,
            reason_code=reason_code.value,
            reason=reason,
            executed=True,
            execution_status=ExecutionStatus.EXECUTED.value,
            result=tool_result,
            approval_id=None
        )
    except Exception as e:
        record_audit_event(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=decision.value,
            reason_code=reason_code.value,
            reason=f"Action allowed by policy, but tool execution failed safely: {str(e)}",
            execution_status=ExecutionStatus.FAILED.value
        )
        return GatewayResponse(
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            destination=request.destination,
            decision=decision.value,
            reason_code=reason_code.value,
            reason=f"Action allowed by policy, but execution encountered an internal error.",
            executed=False,
            execution_status=ExecutionStatus.FAILED.value,
            result={"error": "Simulated tool execution encountered an error."},
            approval_id=None
        )
