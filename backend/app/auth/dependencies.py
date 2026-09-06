from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.config import settings
from backend.app.db.models import AuthSession, Employee
from backend.app.db.session import get_db

from .sessions import hash_session_token


def get_current_employee(
    request: Request,
    db: Session = Depends(get_db),
) -> Employee:
    """Load the active employee associated with the current server-side session."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    session = db.scalar(
        select(AuthSession)
        .options(joinedload(AuthSession.employee).joinedload(Employee.department),
                 joinedload(AuthSession.employee).joinedload(Employee.position))
        .where(AuthSession.token_hash == hash_session_token(token))
    )
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at if session is not None else now
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if session is None or session.revoked_at is not None or expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    if not session.employee.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    session.last_seen_at = now
    db.commit()
    return session.employee
