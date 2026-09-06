from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.audit.events import record_event
from backend.app.auth.authorization import has_permission
from backend.app.auth.dependencies import get_current_employee
from backend.app.auth.passwords import verify_password
from backend.app.db.models import (
    Department,
    Employee,
    EmployeePermissionOverride,
    Permission,
    Position,
    PositionPermission,
)
from backend.app.db.session import get_db

router = APIRouter(prefix="/admin")


class StepUpRequest(BaseModel):
    current_password: str = Field(min_length=1)


class EmployeeUpdateRequest(StepUpRequest):
    department_id: int | None = None
    position_id: int | None = None
    is_active: bool | None = None


class PermissionChangeRequest(StepUpRequest):
    permission_id: int
    allowed: bool


def _require(employee: Employee, db: Session, permission: str) -> None:
    if not has_permission(employee, permission, db):
        record_event(
            db,
            action="UNAUTHORIZED_ADMIN_ATTEMPT",
            result="FAILURE",
            employee=employee,
            resource_type="PERMISSION",
            resource_id=permission,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")


def _step_up(employee: Employee, db: Session, password: str, action: str, target: str) -> None:
    if not verify_password(password, employee.password_hash):
        record_event(
            db,
            action="STEP_UP_AUTHENTICATION",
            result="FAILURE",
            employee=employee,
            resource_type="ADMIN_ACTION",
            resource_id=target,
            details={"action": action},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator verification failed.")
    record_event(
        db,
        action="STEP_UP_AUTHENTICATION",
        result="SUCCESS",
        employee=employee,
        resource_type="ADMIN_ACTION",
        resource_id=target,
        details={"action": action},
    )


def _employee_view(employee: Employee) -> dict:
    return {
        "id": employee.id,
        "employee_id": employee.employee_id,
        "full_name": employee.full_name,
        "department": employee.department.name if employee.department else None,
        "position": employee.position.name if employee.position else None,
        "is_active": employee.is_active,
    }


@router.get("/employees")
def list_employees(
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    _require(employee, db, "USER_VIEW")
    employees = db.scalars(
        select(Employee).options(joinedload(Employee.department), joinedload(Employee.position)).order_by(Employee.employee_id)
    ).all()
    return [_employee_view(item) for item in employees]


@router.get("/positions")
def list_positions(employee: Employee = Depends(get_current_employee), db: Session = Depends(get_db)):
    _require(employee, db, "POSITION_MANAGE")
    return [{"id": item.id, "name": item.name, "department_id": item.department_id, "is_active": item.is_active}
            for item in db.scalars(select(Position).order_by(Position.name)).all()]


@router.get("/permissions")
def list_permissions(employee: Employee = Depends(get_current_employee), db: Session = Depends(get_db)):
    _require(employee, db, "PERMISSION_MANAGE")
    return [{"id": item.id, "code": item.code, "name": item.name, "is_active": item.is_active}
            for item in db.scalars(select(Permission).order_by(Permission.code)).all()]


@router.patch("/employees/{target_id}")
def update_employee(
    target_id: int,
    payload: EmployeeUpdateRequest,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    target = db.get(Employee, target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    if payload.is_active is not None:
        _require(employee, db, "USER_DISABLE")
    if payload.department_id is not None or payload.position_id is not None:
        _require(employee, db, "USER_UPDATE")
    _step_up(employee, db, payload.current_password, "EMPLOYEE_UPDATED", str(target_id))
    if payload.department_id is not None:
        target.department_id = payload.department_id
    if payload.position_id is not None:
        target.position_id = payload.position_id
    if payload.is_active is not None:
        target.is_active = payload.is_active
    db.commit()
    action = "EMPLOYEE_ENABLED" if payload.is_active else "EMPLOYEE_DISABLED"
    record_event(db, action=action, result="SUCCESS", employee=employee, resource_type="EMPLOYEE", resource_id=target.employee_id)
    db.commit()
    return _employee_view(target)


@router.put("/employees/{target_id}/overrides")
def set_employee_override(
    target_id: int,
    payload: PermissionChangeRequest,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    _require(employee, db, "USER_UPDATE")
    target = db.get(Employee, target_id)
    permission = db.get(Permission, payload.permission_id)
    if target is None or permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found.")
    _step_up(employee, db, payload.current_password, "EMPLOYEE_PERMISSION_CHANGED", target.employee_id)
    override = db.scalar(select(EmployeePermissionOverride).where(
        EmployeePermissionOverride.employee_id == target.id,
        EmployeePermissionOverride.permission_id == permission.id,
    ))
    if override is None:
        override = EmployeePermissionOverride(employee_id=target.id, permission_id=permission.id, allowed=payload.allowed)
        db.add(override)
    else:
        override.allowed = payload.allowed
    db.commit()
    event = "EMPLOYEE_PERMISSION_GRANTED" if payload.allowed else "EMPLOYEE_PERMISSION_REVOKED"
    record_event(db, action=event, result="SUCCESS", employee=employee, resource_type="EMPLOYEE_PERMISSION", resource_id=target.employee_id)
    db.commit()
    return {"employee_id": target.employee_id, "permission": permission.code, "allowed": payload.allowed}


@router.put("/positions/{position_id}/permissions")
def set_position_permission(
    position_id: int,
    payload: PermissionChangeRequest,
    employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    _require(employee, db, "POSITION_MANAGE")
    position = db.get(Position, position_id)
    permission = db.get(Permission, payload.permission_id)
    if position is None or permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found.")
    _step_up(employee, db, payload.current_password, "POSITION_PERMISSION_CHANGED", str(position_id))
    assignment = db.scalar(select(PositionPermission).where(
        PositionPermission.position_id == position.id,
        PositionPermission.permission_id == permission.id,
    ))
    if assignment is None:
        assignment = PositionPermission(position_id=position.id, permission_id=permission.id, allowed=payload.allowed)
        db.add(assignment)
    else:
        assignment.allowed = payload.allowed
    db.commit()
    event = "POSITION_PERMISSION_GRANTED" if payload.allowed else "POSITION_PERMISSION_REVOKED"
    record_event(
        db,
        action=event,
        result="SUCCESS",
        employee=employee,
        resource_type="POSITION_PERMISSION",
        resource_id=f"{position.name}/{permission.code}",
    )
    db.commit()
    return {"position": position.name, "permission": permission.code, "allowed": payload.allowed}
