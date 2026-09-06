import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db.models import AuthSession, Employee


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, employee: Employee) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    db.add(
        AuthSession(
            token_hash=hash_session_token(token),
            employee_id=employee.id,
            created_at=now,
            expires_at=now + timedelta(seconds=settings.SESSION_LIFETIME_SECONDS),
            last_seen_at=now,
        )
    )
    db.commit()
    return token
