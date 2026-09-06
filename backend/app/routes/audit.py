from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.auth.authorization import require_permission
from backend.app.db.models import AuditEvent, Employee
from backend.app.db.session import get_db

router = APIRouter()


@router.get("/audit")
def get_audit_events(
    employee: Employee = Depends(require_permission("AUDIT_VIEW")),
    db: Session = Depends(get_db),
):
    events = db.scalars(
        select(AuditEvent)
        .options(joinedload(AuditEvent.employee).joinedload(Employee.department),
                 joinedload(AuditEvent.employee).joinedload(Employee.position))
        .order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc())
        .limit(500)
    ).all()
    return {
        "source": "postgresql",
        "events": [
            {
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "employee_id": event.employee.employee_id if event.employee else None,
                "employee_name": event.employee.full_name if event.employee else None,
                "department": event.employee.department.name if event.employee and event.employee.department else None,
                "position": event.employee.position.name if event.employee and event.employee.position else None,
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "result": event.result,
                "details": event.details,
                "request_id": event.request_id,
            }
            for event in events
        ],
    }