from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from backend.app.audit.audit import AuditLogger
from backend.app.db.models import AuditEvent, Employee


def record_event(
    db: Session,
    *,
    action: str,
    result: str,
    employee: Employee | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: Mapping[str, Any] | None = None,
    request_id: str | None = None,
) -> AuditEvent:
    safe_details = AuditLogger._sanitize_value(dict(details or {}))
    event = AuditEvent(
        employee_id=employee.id if employee else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        details=safe_details,
        request_id=request_id,
    )
    db.add(event)
    db.flush()
    return event
