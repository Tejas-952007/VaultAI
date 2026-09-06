from datetime import datetime
from typing import List, Dict

# Simple in-memory audit store for sandbox executions
# In production this would be persisted to a DB.
_sandbox_audit_log: List[Dict] = []

async def record_sandbox_audit(
    request_id: str,
    language: str,
    timestamp: datetime,
    duration_seconds: float,
    exit_code: int,
    timed_out: bool,
    error_message: str | None = None,
) -> None:
    """Record an audit entry for a sandbox execution.
    The function stores the entry in an in-memory list; this is sufficient for the prototype.
    """
    entry = {
        "request_id": request_id,
        "language": language,
        "timestamp": timestamp.isoformat(),
        "duration_seconds": duration_seconds,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "error_message": error_message,
    }
    _sandbox_audit_log.append(entry)

def get_sandbox_audit_log() -> List[Dict]:
    """Return a copy of the audit log for inspection/testing."""
    return list(_sandbox_audit_log)
