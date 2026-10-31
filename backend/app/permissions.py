"""Agent permissions and explicit allow-lists for KAWACH / AGENTSHIELD.

Defines role-based access control policies for registered agents:
- research_assistant
- project_manager

Permissions are never inferred from task wording or prompts.
Unregistered agents, tools, or actions fail closed.
"""

from typing import Dict, Any, List

KNOWN_AGENTS: Dict[str, str] = {
    "research_assistant": "Research Assistant",
    "project_manager": "Project Manager"
}

# Explicit Tool Registry
KNOWN_TOOLS: Dict[str, List[str]] = {
    "document_reader": ["read"],
    "file_manager": ["list", "delete"],
    "email_sender": ["send", "draft"]
}

# Agent Role Permission Rules
# Explicit capability definitions
AGENT_PERMISSIONS: Dict[str, Dict[str, List[str]]] = {
    "research_assistant": {
        "document_reader": ["read"],
        "file_manager": ["list"],
        "email_sender": []
    },
    "project_manager": {
        "document_reader": ["read"],
        "file_manager": ["list"],
        "email_sender": ["draft", "send"]
    }
}


def is_known_agent(agent_id: str) -> bool:
    """Checks if agent_id is in the known agents directory."""
    return agent_id in KNOWN_AGENTS


def is_known_tool(tool: str) -> bool:
    """Checks if tool is in the known tools registry."""
    return tool in KNOWN_TOOLS


def is_known_action(tool: str, action: str) -> bool:
    """Checks if action is valid for the given tool."""
    return tool in KNOWN_TOOLS and action in KNOWN_TOOLS[tool]


def agent_has_tool_permission(agent_id: str, tool: str, action: str) -> bool:
    """Checks whether the agent has explicit permission for the tool action."""
    if not is_known_agent(agent_id):
        return False
    agent_perms = AGENT_PERMISSIONS.get(agent_id, {})
    tool_actions = agent_perms.get(tool, [])
    return action in tool_actions
