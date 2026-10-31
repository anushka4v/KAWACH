"""Resource registry and sensitivity classification for KAWACH / AGENTSHIELD.

Maps exact resource names to security tiers:
PUBLIC, INTERNAL, INTERNAL_UNTRUSTED, CONFIDENTIAL, SECRET.
Arbitrary paths and unregistered resources are strictly rejected.
"""

from typing import Optional, Dict

RESOURCE_REGISTRY: Dict[str, str] = {
    "public_project_info.pdf": "PUBLIC",
    "NovaTech_Project_Report.pdf": "INTERNAL",
    "NovaTech_Research_Report.pdf": "INTERNAL_UNTRUSTED",
    "NovaTech_Financial_Report.pdf": "CONFIDENTIAL",
    "employee_records.csv": "CONFIDENTIAL",
    "api_credentials.txt": "SECRET",
}

# Classification Hierarchy for reference
# PUBLIC < INTERNAL < INTERNAL_UNTRUSTED < CONFIDENTIAL < SECRET


def get_resource_classification(resource_name: Optional[str]) -> Optional[str]:
    """Returns the security classification of an exact registered resource.
    
    Returns None if resource_name is None, empty, or not in the fixed registry.
    Path characters (/ or \\) are rejected.
    """
    if not resource_name or not isinstance(resource_name, str):
        return None
    
    # Reject path traversal attempts immediately
    if "/" in resource_name or "\\" in resource_name or ".." in resource_name:
        return None
        
    return RESOURCE_REGISTRY.get(resource_name)


def is_registered_resource(resource_name: str) -> bool:
    """Checks whether a resource name is registered in the fixed registry."""
    return get_resource_classification(resource_name) is not None
