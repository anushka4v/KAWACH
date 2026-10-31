"""Simulated Document Reader Tool.

Reads from an in-memory dictionary of fictional synthetic documents.
Never reads arbitrary filesystem paths.
"""

from typing import Dict, Any
from data.seed_data import DEFAULT_DOCUMENTS, tool_counters


def read(resource: str) -> Dict[str, Any]:
    """Reads a permitted document from the synthetic document store."""
    if resource not in DEFAULT_DOCUMENTS:
        return {
            "success": False,
            "error": f"Resource '{resource}' not found in registered document store."
        }

    # Increment execution counter
    tool_counters["document_reader.read"] += 1

    return {
        "success": True,
        "resource": resource,
        "content": DEFAULT_DOCUMENTS[resource]
    }
