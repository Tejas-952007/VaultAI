import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app.auth.authorization import has_permission, require_permission
from backend.app.auth.permissions import PermissionCode
from backend.app.auth.passwords import hash_password
from backend.app.db.seed import seed_demo_data
from backend.app.db.base import Base
from backend.app.db.models import (
    Department,
    Employee,
    EmployeePermissionOverride,
    Permission,
    Position,
    PositionPermission,
)


@pytest.fixture
def authorization_context():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db:
        department = Department(name="Engineering")
        clerk = Position(name="Clerk", department=department)
        administrator = Position(name="Administrator", department=department)
        document_view = Permission(code=PermissionCode.DOCUMENT_VIEW, name="Document View")
        report_export = Permission(code=PermissionCode.REPORT_EXPORT, name="Report Export")
        position_deny = Permission(code=PermissionCode.CODE_GENERATE, name="Code Generate")
        db.add_all([department, clerk, administrator, document_view, report_export, position_deny])
        db.flush()
        db.add(PositionPermission(position=clerk, permission=document_view, allowed=True))
        employee = Employee(
            employee_id="EMP001",
            full_name="Employee",
            password_hash=hash_password("not-used"),
            department=department,
            position=clerk,
        )
        inactive = Employee(
            employee_id="INACTIVE",
            full_name="Inactive",
            password_hash=hash_password("not-used"),
            department=department,
            position=clerk,
            is_active=False,
        )
        admin = Employee(
            employee_id="ADMIN001",
            full_name="Administrator",
            password_hash=hash_password("not-used"),
            department=department,
            position=administrator,
        )
        db.add_all([employee, inactive, admin])
        db.commit()
        yield db, employee, inactive, admin, document_view, report_export, position_deny


def test_position_permission_allows_and_missing_permission_denies(authorization_context):
    db, employee, _, _, _, _, _ = authorization_context
    assert has_permission(employee, "DOCUMENT_VIEW", db)
    assert not has_permission(employee, "DOCUMENT_DOWNLOAD", db)
    assert not has_permission(employee, "UNKNOWN_PERMISSION", db)


def test_inactive_employee_is_denied(authorization_context):
    db, _, inactive, _, _, _, _ = authorization_context
    assert not has_permission(inactive, "DOCUMENT_VIEW", db)


def test_employee_deny_override_beats_position_allow(authorization_context):
    db, employee, _, _, document_view, _, _ = authorization_context
    db.add(EmployeePermissionOverride(employee_id=employee.id, permission_id=document_view.id, allowed=False))
    db.commit()
    assert not has_permission(employee, "DOCUMENT_VIEW", db)


def test_employee_allow_override_beats_position_deny(authorization_context):
    db, employee, _, _, _, report_export, _ = authorization_context
    db.add(PositionPermission(position_id=employee.position_id, permission_id=report_export.id, allowed=False))
    db.add(EmployeePermissionOverride(employee_id=employee.id, permission_id=report_export.id, allowed=True))
    db.commit()
    assert has_permission(employee, "REPORT_EXPORT", db)


def test_changing_position_permission_changes_authorization(authorization_context):
    db, employee, _, _, _, report_export, _ = authorization_context
    assert not has_permission(employee, "REPORT_EXPORT", db)
    db.add(PositionPermission(position_id=employee.position_id, permission_id=report_export.id, allowed=True))
    db.commit()
    assert has_permission(employee, "REPORT_EXPORT", db)


def test_administrator_does_not_bypass_permission_engine(authorization_context):
    db, _, _, administrator, _, _, _ = authorization_context
    assert not has_permission(administrator, "SYSTEM_ADMIN", db)


def test_require_permission_returns_generic_forbidden(authorization_context):
    db, employee, _, _, _, _, _ = authorization_context
    dependency = require_permission("DOCUMENT_DOWNLOAD")
    with pytest.raises(HTTPException) as error:
        dependency(employee=employee, db=db)
    assert error.value.status_code == 403
    assert error.value.detail == "Insufficient permissions."


def test_position_is_loaded_from_database_not_client_input(authorization_context):
    db, employee, _, _, _, _, _ = authorization_context
    assert employee.position.name == "Clerk"
    assert not has_permission(employee, "SYSTEM_ADMIN", db)


def test_demo_seed_populates_database_backed_position_permissions():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        seed_demo_data(db)
        clerk = db.scalar(select(Position).where(Position.name == "Clerk"))
        document_view = db.scalar(select(Permission).where(Permission.code == "DOCUMENT_VIEW"))
        report_export = db.scalar(select(Permission).where(Permission.code == "REPORT_EXPORT"))
        assert db.scalar(
            select(PositionPermission).where(
                PositionPermission.position_id == clerk.id,
                PositionPermission.permission_id == document_view.id,
                PositionPermission.allowed.is_(True),
            )
        ) is not None
        assert db.scalar(
            select(PositionPermission).where(
                PositionPermission.position_id == clerk.id,
                PositionPermission.permission_id == report_export.id,
            )
        ) is None
