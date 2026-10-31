"""Simulated File Manager Tool.

Operates strictly on an in-memory list of demo files.
No real filesystem operations (no os.remove, pathlib.Path.unlink, shutil.rmtree).
"""

from typing import Dict, Any, List
from data.seed_data import simulated_files, tool_counters


def list_files() -> Dict[str, Any]:
    """Returns the list of currently available simulated files."""
    tool_counters["file_manager.list"] += 1
    return {
        "success": True,
        "files": list(simulated_files),
        "count": len(simulated_files)
    }


def delete_file(resource: str) -> Dict[str, Any]:
    """Removes a file from the simulated in-memory list only."""
    tool_counters["file_manager.delete"] += 1
    if resource in simulated_files:
        simulated_files.remove(resource)
        return {
            "success": True,
            "message": f"Simulated file '{resource}' successfully removed from demo catalog.",
            "remaining_files": list(simulated_files)
        }
    return {
        "success": False,
        "error": f"Simulated file '{resource}' was not found in demo file catalog.",
        "remaining_files": list(simulated_files)
    }
