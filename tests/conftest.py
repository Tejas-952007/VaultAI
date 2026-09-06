import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.auth.passwords import hash_password
from backend.app.db.base import Base
from backend.app.db.models import Department, Employee, Permission, Position, PositionPermission
from backend.app.db.session import get_db
from backend.app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def authenticated_client():
    """Client with a database-backed employee granted endpoint test permissions."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db:
        department = Department(name="Test Department")
        position = Position(name="Test Operator", department=department)
        permissions = [
            Permission(code=code, name=code.replace("_", " ").title())
            for code in (
                "DOCUMENT_VIEW",
                "DOCUMENT_UPLOAD",
                "RAG_QUERY",
                "CODE_GENERATE",
                "VISION_ANALYSIS",
            )
        ]
        db.add_all([department, position, *permissions])
        db.flush()
        db.add_all([
            PositionPermission(position_id=position.id, permission_id=permission.id, allowed=True)
            for permission in permissions
        ])
        employee = Employee(
            employee_id="TEST001",
            full_name="Endpoint Test Employee",
            password_hash=hash_password("test-password"),
            department=department,
            position=position,
        )
        db.add(employee)
        db.commit()

    def override_get_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/auth/login",
            json={"employee_id": "TEST001", "password": "test-password"},
        )
        assert response.status_code == 200
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def permissionless_client():
    """Client authenticated as an employee with no endpoint permissions."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db:
        department = Department(name="Limited Department")
        position = Position(name="Limited Operator", department=department)
        employee = Employee(
            employee_id="LIMITED001",
            full_name="Limited Employee",
            password_hash=hash_password("test-password"),
            department=department,
            position=position,
        )
        db.add_all([department, position, employee])
        db.commit()

    def override_get_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/auth/login",
            json={"employee_id": "LIMITED001", "password": "test-password"},
        )
        assert response.status_code == 200
        yield test_client
    app.dependency_overrides.clear()
