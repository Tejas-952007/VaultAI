from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.auth.dependencies import get_current_employee
from backend.app.auth.passwords import verify_password
from backend.app.auth.sessions import create_session, hash_session_token
from backend.app.audit.events import record_event
from backend.app.config import settings
from backend.app.db.models import AuthSession, Employee
from backend.app.db.session import get_db
from backend.app.rate_limit import auth_limiter

router = APIRouter(prefix="/auth")
INVALID_LOGIN_MESSAGE = "Invalid employee ID or password."


class LoginRequest(BaseModel):
    employee_id: str = Field(min_length=1)
    password: str = Field(min_length=1)


class EmployeeIdentity(BaseModel):
    employee_id: str
    full_name: str
    department: str | None
    position: str | None
    is_active: bool


class AuthResponse(BaseModel):
    authenticated: bool
    employee: EmployeeIdentity


def _identity(employee: Employee) -> EmployeeIdentity:
    return EmployeeIdentity(
        employee_id=employee.employee_id,
        full_name=employee.full_name,
        department=employee.department.name if employee.department else None,
        position=employee.position.name if employee.position else None,
        is_active=employee.is_active,
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    if not auth_limiter.allow(payload.employee_id.strip().lower()):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts. Try again shortly.")

    employee = db.scalar(
        select(Employee)
        .options(joinedload(Employee.department), joinedload(Employee.position))
        .where(Employee.employee_id == payload.employee_id.strip())
    )
    if employee is None or not employee.is_active or not verify_password(payload.password, employee.password_hash):
        record_event(
            db,
            action="LOGIN",
            result="FAILURE",
            employee=employee,
            resource_type="AUTHENTICATION",
            details={"reason": "invalid_credentials"},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_LOGIN_MESSAGE)

    token = create_session(db, employee)
    record_event(db, action="LOGIN", result="SUCCESS", employee=employee, resource_type="AUTHENTICATION")
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_LIFETIME_SECONDS,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        path=settings.API_V1_STR,
    )
    return AuthResponse(authenticated=True, employee=_identity(employee))


@router.get("/me", response_model=AuthResponse)
def me(employee: Employee = Depends(get_current_employee)):
    return AuthResponse(authenticated=True, employee=_identity(employee))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    employee = None
    if token:
        session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_session_token(token)))
        if session and session.revoked_at is None:
            employee = session.employee
            session.revoked_at = datetime.now(timezone.utc)
            record_event(db, action="LOGOUT", result="SUCCESS", employee=employee, resource_type="AUTHENTICATION")
            db.commit()
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path=settings.API_V1_STR,
    )
