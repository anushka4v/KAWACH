"""Simulated Email Sender Tool.

Appends messages to in-memory lists (mock_sent_emails, mock_draft_emails).
Never connects to SMTP, Gmail, Outlook, or any network service.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from data.seed_data import mock_sent_emails, mock_draft_emails, tool_counters


def send_email(recipient: str, subject: str, body: str) -> Dict[str, Any]:
    """Appends an email entry to the in-memory mock_sent_emails store."""
    tool_counters["email_sender.send"] += 1
    email_record = {
        "id": f"email_{len(mock_sent_emails) + 1}",
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    mock_sent_emails.append(email_record)
    return {
        "success": True,
        "message": f"Simulated email sent to {recipient}.",
        "email_record": email_record,
        "total_sent_count": len(mock_sent_emails)
    }


def draft_email(recipient: str, subject: str, body: str) -> Dict[str, Any]:
    """Appends an email draft to the in-memory mock_draft_emails store."""
    tool_counters["email_sender.draft"] += 1
    draft_record = {
        "id": f"draft_{len(mock_draft_emails) + 1}",
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    mock_draft_emails.append(draft_record)
    return {
        "success": True,
        "message": f"Simulated email draft saved for {recipient}.",
        "draft_record": draft_record,
        "total_draft_count": len(mock_draft_emails)
    }
