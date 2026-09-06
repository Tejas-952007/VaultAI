from collections.abc import Callable
import json

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_employee
from backend.app.auth.permissions import PERMISSION_CODES
from backend.app.db.models import Employee, EmployeePermissionOverride, Permission, PositionPermission
from backend.app.db.session import get_db
from backend.app.graph.router import classify_route


def has_permission(employee: Employee, permission_code: str, db: Session) -> bool:
    """Evaluate one permission using deny-by-default precedence."""
    if not employee.is_active or permission_code not in PERMISSION_CODES:
        return False

    permission = db.scalar(select(Permission).where(Permission.code == permission_code, Permission.is_active.is_(True)))
    if permission is None:
        return False

    override = db.scalar(
        select(EmployeePermissionOverride).where(
            EmployeePermissionOverride.employee_id == employee.id,
            EmployeePermissionOverride.permission_id == permission.id,
        )
    )
    if override is not None:
        return override.allowed

    if employee.position_id is None:
        return False
    position_permission = db.scalar(
        select(PositionPermission).where(
            PositionPermission.position_id == employee.position_id,
            PositionPermission.permission_id == permission.id,
        )
    )
    return bool(position_permission and position_permission.allowed)


def require_permission(permission_code: str) -> Callable:
    """Create a FastAPI dependency enforcing one database-backed permission."""
    def dependency(
        employee: Employee = Depends(get_current_employee),
        db: Session = Depends(get_db),
    ) -> Employee:
        if not has_permission(employee, permission_code, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return employee

    return dependency


async def require_chat_permission(
    request: Request,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> Employee:
    """Authorize chat based on the route selected from the submitted request."""
    body = await request.body()
    request._body = body
    try:
        payload = json.loads(body)
    except (TypeError, ValueError):
        payload = {}
    route = classify_route(payload.get("message", ""), payload.get("document_ids"))
    permission = {
        "document": "RAG_QUERY",
        "coding": "CODE_GENERATE",
        "vision": "VISION_ANALYSIS",
    }.get(route, "RAG_QUERY")
    if not has_permission(employee, permission, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    return employee
