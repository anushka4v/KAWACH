"""Deterministic Pure Policy Evaluation Engine for KAWACH / AGENTSHIELD.

Evaluates proposed tool requests against deterministic allow-lists,
role definitions, resource classifications, and boundary conditions.
NEVER executes any tool. Pure, deterministic, fail-closed.
"""

from typing import Tuple, Optional, Dict, Any
from app.resources import get_resource_classification, is_registered_resource
from app.permissions import (
    is_known_agent,
    is_known_tool,
    is_known_action,
    agent_has_tool_permission
)
from app.schemas import DecisionType, ReasonCode


def is_external_destination(destination: Optional[str]) -> bool:
    """Checks whether a destination address is external.
    
    Any address that is not within the simulated '@novatech.internal' domain is treated as external.
    """
    if not destination or not isinstance(destination, str):
        return False
    clean_dest = destination.strip().lower()
    return not clean_dest.endswith("@novatech.internal")


def evaluate_policy(
    agent_id: str,
    tool: str,
    action: str,
    resource: Optional[str] = None,
    destination: Optional[str] = None,
    arguments: Optional[Dict[str, Any]] = None
) -> Tuple[DecisionType, ReasonCode, str]:
    """Pure deterministic policy evaluation.
    
    Returns (decision, reason_code, reason).
    Fails closed on any unknown parameter or boundary violation.
    """
    # 1. Validate agent identity
    if not is_known_agent(agent_id):
        return (
            DecisionType.DENY,
            ReasonCode.UNKNOWN_AGENT,
            f"Agent identity '{agent_id}' is not recognized in the security directory."
        )

    # 2. Validate tool registry
    if not is_known_tool(tool):
        return (
            DecisionType.DENY,
            ReasonCode.UNKNOWN_TOOL,
            f"Tool '{tool}' is not registered in the approved tool directory."
        )

    # 3. Validate action on tool
    if not is_known_action(tool, action):
        return (
            DecisionType.DENY,
            ReasonCode.ACTION_NOT_ALLOWED,
            f"Action '{action}' is not supported or defined for tool '{tool}'."
        )

    # 4. Validate resource if specified
    classification: Optional[str] = None
    if resource is not None:
        if not is_registered_resource(resource):
            return (
                DecisionType.DENY,
                ReasonCode.UNKNOWN_RESOURCE,
                f"Resource '{resource}' is not recognized or not registered in the resource catalog."
            )
        classification = get_resource_classification(resource)

        # Immediate rule: SECRET resources can never be read or transmitted by any agent
        if classification == "SECRET":
            return (
                DecisionType.DENY,
                ReasonCode.RESOURCE_SECRET,
                f"Access to SECRET resource '{resource}' is strictly forbidden by gateway baseline policy."
            )

    # 5. Role-specific policy evaluation
    if agent_id == "research_assistant":
        # Tool: file_manager
        if tool == "file_manager":
            if action == "list":
                return (
                    DecisionType.ALLOW,
                    ReasonCode.PERMISSION_GRANTED,
                    "Simulated directory file listing is permitted for Research Assistant."
                )
            elif action == "delete":
                return (
                    DecisionType.DENY,
                    ReasonCode.ACTION_NOT_ALLOWED,
                    "Agent 'research_assistant' does not possess file deletion authority."
                )
            else:
                return (
                    DecisionType.DENY,
                    ReasonCode.ACTION_NOT_ALLOWED,
                    f"Action '{action}' on 'file_manager' is not permitted for Research Assistant."
                )

        # Tool: email_sender
        elif tool == "email_sender":
            return (
                DecisionType.DENY,
                ReasonCode.TOOL_NOT_ALLOWED,
                "Agent 'research_assistant' is strictly forbidden from using email communications."
            )

        # Tool: document_reader
        elif tool == "document_reader":
            if action == "read":
                if resource is None:
                    return (
                        DecisionType.DENY,
                        ReasonCode.INVALID_REQUEST,
                        "Document reader requires an explicit resource target."
                    )
                
                # Public documents are always allowed
                if classification == "PUBLIC":
                    return (
                        DecisionType.ALLOW,
                        ReasonCode.PERMISSION_GRANTED,
                        f"Read access to PUBLIC resource '{resource}' granted to Research Assistant."
                    )
                
                # Special fixture for Demo 2 (untrusted incoming email fixture)
                if resource == "NovaTech_Research_Report.pdf" and classification == "INTERNAL_UNTRUSTED":
                    return (
                        DecisionType.ALLOW,
                        ReasonCode.PERMISSION_GRANTED,
                        "Read access to incoming research fixture granted for analysis (treated as untrusted data)."
                    )

                # Internal or confidential resources are denied to research_assistant
                return (
                    DecisionType.DENY,
                    ReasonCode.RESOURCE_CONFIDENTIAL,
                    f"Research Assistant lacks clearance to read {classification} resource '{resource}'."
                )
            else:
                return (
                    DecisionType.DENY,
                    ReasonCode.ACTION_NOT_ALLOWED,
                    f"Action '{action}' on document_reader not supported."
                )

        # Fail closed for any other tool
        return (
            DecisionType.DENY,
            ReasonCode.TOOL_NOT_ALLOWED,
            f"Tool '{tool}' not permitted for Research Assistant."
        )

    elif agent_id == "project_manager":
        # Tool: document_reader
        if tool == "document_reader":
            if action == "read":
                if resource is None:
                    return (
                        DecisionType.DENY,
                        ReasonCode.INVALID_REQUEST,
                        "Document reader requires an explicit resource target."
                    )
                if classification in ["PUBLIC", "INTERNAL", "INTERNAL_UNTRUSTED"]:
                    return (
                        DecisionType.ALLOW,
                        ReasonCode.PERMISSION_GRANTED,
                        f"Read access to {classification} resource '{resource}' granted to Project Manager."
                    )
                # Confidential resources cannot be read directly without proper role
                return (
                    DecisionType.DENY,
                    ReasonCode.RESOURCE_CONFIDENTIAL,
                    f"Project Manager direct read of CONFIDENTIAL resource '{resource}' is denied by default."
                )
            else:
                return (
                    DecisionType.DENY,
                    ReasonCode.ACTION_NOT_ALLOWED,
                    f"Action '{action}' on document_reader not permitted for Project Manager."
                )

        # Tool: file_manager
        elif tool == "file_manager":
            if action == "list":
                return (
                    DecisionType.ALLOW,
                    ReasonCode.PERMISSION_GRANTED,
                    "File listing permitted for Project Manager."
                )
            elif action == "delete":
                return (
                    DecisionType.DENY,
                    ReasonCode.ACTION_NOT_ALLOWED,
                    "File deletion is disabled by default for Project Manager."
                )
            else:
                return (
                    DecisionType.DENY,
                    ReasonCode.ACTION_NOT_ALLOWED,
                    f"Action '{action}' on file_manager not permitted."
                )

        # Tool: email_sender
        elif tool == "email_sender":
            if action == "draft":
                return (
                    DecisionType.ALLOW,
                    ReasonCode.PERMISSION_GRANTED,
                    "Simulated email drafting permitted for Project Manager."
                )
            elif action == "send":
                # Check for high-impact action requiring human approval:
                # External sharing of a CONFIDENTIAL resource
                is_ext = is_external_destination(destination)
                if classification == "CONFIDENTIAL" and is_ext:
                    return (
                        DecisionType.REQUIRE_APPROVAL,
                        ReasonCode.APPROVAL_REQUIRED,
                        f"External dispatch of CONFIDENTIAL resource '{resource}' to destination '{destination}' requires mandatory human confirmation."
                    )
                elif classification == "CONFIDENTIAL":
                    # Internal send of confidential document
                    return (
                        DecisionType.REQUIRE_APPROVAL,
                        ReasonCode.APPROVAL_REQUIRED,
                        f"Transmission of CONFIDENTIAL resource '{resource}' requires human authorization."
                    )
                elif is_ext:
                    # External send of non-confidential content
                    return (
                        DecisionType.REQUIRE_APPROVAL,
                        ReasonCode.APPROVAL_REQUIRED,
                        f"Outbound external transmission to '{destination}' requires human confirmation."
                    )
                else:
                    return (
                        DecisionType.ALLOW,
                        ReasonCode.PERMISSION_GRANTED,
                        "Internal routine email dispatch permitted for Project Manager."
                    )
            else:
                return (
                    DecisionType.DENY,
                    ReasonCode.ACTION_NOT_ALLOWED,
                    f"Action '{action}' on email_sender not permitted."
                )

        # Fail closed
        return (
            DecisionType.DENY,
            ReasonCode.TOOL_NOT_ALLOWED,
            f"Tool '{tool}' not permitted for Project Manager."
        )

    # Fail closed for any unhandled state
    return (
        DecisionType.DENY,
        ReasonCode.TOOL_NOT_ALLOWED,
        f"Unauthorized action for agent '{agent_id}'."
    )
