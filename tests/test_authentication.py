from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.auth.passwords import hash_password, verify_password
from backend.app.auth.sessions import hash_session_token
from backend.app.db.base import Base
from backend.app.db.models import AuthSession, Department, Employee, Position
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.rate_limit import auth_limiter


@pytest.fixture
def auth_context():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db:
        department = Department(name="Administration")
        position = Position(name="Clerk", department=department)
        employee = Employee(
            employee_id="EMP001",
            full_name="Test Employee",
            password_hash=hash_password("correct-password"),
            department=department,
            position=position,
        )
        inactive = Employee(
            employee_id="INACTIVE",
            full_name="Inactive Employee",
            password_hash=hash_password("correct-password"),
            is_active=False,
        )
        db.add_all([department, position, employee, inactive])
        db.commit()

    def override_get_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    auth_limiter._buckets.clear()
    with TestClient(app) as client:
        yield client, session_factory
    app.dependency_overrides.clear()
    auth_limiter._buckets.clear()


def test_password_hashing_and_verification():
    password_hash = hash_password("secret")
    assert password_hash.startswith("$argon2id$")
    assert password_hash != "secret"
    assert verify_password("secret", password_hash)
    assert not verify_password("wrong", password_hash)
    assert hash_password("secret") != password_hash
    assert not verify_password("secret", "malformed-hash")
    with pytest.raises(ValueError):
        hash_password("")


def test_login_creates_session_and_returns_only_safe_identity(auth_context):
    client, session_factory = auth_context
    response = client.post("/api/v1/auth/login", json={"employee_id": "EMP001", "password": "correct-password"})
    assert response.status_code == 200
    body = response.json()
    assert body["employee"]["department"] == "Administration"
    assert body["employee"]["position"] == "Clerk"
    assert "password_hash" not in body
    assert "token" not in body
    assert "vaultai_session" in response.cookies
    with session_factory() as db:
        sessions = db.scalars(select(AuthSession)).all()
        assert len(sessions) == 1
        assert sessions[0].token_hash != response.cookies["vaultai_session"]


def test_me_uses_database_identity_and_logout_revokes_session(auth_context):
    client, session_factory = auth_context
    login = client.post("/api/v1/auth/login", json={"employee_id": "EMP001", "password": "correct-password"})
    assert client.get("/api/v1/auth/me").json()["employee"]["employee_id"] == "EMP001"
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    with session_factory() as db:
        session = db.scalar(select(AuthSession))
        assert session.revoked_at is not None


def test_invalid_unknown_and_inactive_credentials_are_generic(auth_context):
    client, _ = auth_context
    expected = "Invalid employee ID or password."
    wrong = client.post("/api/v1/auth/login", json={"employee_id": "EMP001", "password": "wrong"})
    unknown = client.post("/api/v1/auth/login", json={"employee_id": "UNKNOWN", "password": "wrong"})
    inactive = client.post("/api/v1/auth/login", json={"employee_id": "INACTIVE", "password": "correct-password"})
    assert [item.status_code for item in (wrong, unknown, inactive)] == [401, 401, 401]
    assert [item.json()["detail"] for item in (wrong, unknown, inactive)] == [expected] * 3


def test_expired_session_and_unauthenticated_me_are_rejected(auth_context):
    client, session_factory = auth_context
    assert client.get("/api/v1/auth/me").status_code == 401
    token = "test-token"
    with session_factory() as db:
        employee = db.scalar(select(Employee).where(Employee.employee_id == "EMP001"))
        db.add(AuthSession(token_hash=hash_session_token(token), employee_id=employee.id,
                           created_at=datetime.now(timezone.utc) - timedelta(hours=1),
                           expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
        db.commit()
    client.cookies.set("vaultai_session", token)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_rate_limit_blocks_excessive_attempts(auth_context):
    client, _ = auth_context
    for _ in range(10):
        assert client.post("/api/v1/auth/login", json={"employee_id": "EMP001", "password": "wrong"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"employee_id": "EMP001", "password": "wrong"}).status_code == 429
