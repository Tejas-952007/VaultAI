from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from backend.app.config import Settings
from backend.app.db.base import Base
from backend.app.db.models import Department, Employee, EmployeePermissionOverride, Permission, Position, PositionPermission


def test_database_configuration_loads_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")
    assert Settings().DATABASE_URL.endswith("/test")


def test_models_create_and_relationships_work_on_isolated_sqlite_database():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        department = Department(name="Demo Operations")
        position = Position(name="Demo Engineer", department=department)
        permission = Permission(code="DEMO_VIEW", name="Demo View")
        employee = Employee(employee_id="D-001", full_name="Demo User", password_hash="argon2id-placeholder",
                            department=department, position=position)
        position_permission = PositionPermission(position=position, permission=permission, allowed=True)
        override = EmployeePermissionOverride(employee=employee, permission=permission, allowed=False)
        session.add_all([department, position, permission, employee, position_permission, override])
        session.commit()
        assert employee.department.name == "Demo Operations"
        assert position.position_permissions[0].permission.code == "DEMO_VIEW"
        assert employee.permission_overrides[0].allowed is False


def test_required_schema_constraints_and_columns_exist():
    tables = Base.metadata.tables
    assert {"departments", "positions", "permissions", "employees", "position_permissions", "employee_permission_overrides"} <= tables.keys()
    assert "password_hash" in tables["employees"].c
    assert "is_active" in tables["employees"].c
    assert "password" not in tables["employees"].c
    assert tables["employees"].c.employee_id.unique is True
    assert tables["permissions"].c.code.unique is True
    assert {fk.target_fullname for fk in tables["employees"].c.department_id.foreign_keys} == {"departments.id"}
    assert {fk.target_fullname for fk in tables["employees"].c.position_id.foreign_keys} == {"positions.id"}
    assert {fk.target_fullname for fk in tables["position_permissions"].c.position_id.foreign_keys} == {"positions.id"}
    assert {fk.target_fullname for fk in tables["position_permissions"].c.permission_id.foreign_keys} == {"permissions.id"}
    assert {fk.target_fullname for fk in tables["employee_permission_overrides"].c.employee_id.foreign_keys} == {"employees.id"}
    assert {fk.target_fullname for fk in tables["employee_permission_overrides"].c.permission_id.foreign_keys} == {"permissions.id"}

