import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.auth.passwords import hash_password
from backend.app.db.models import Department, Employee, Permission, Position, PositionPermission

DEMO_DEPARTMENTS = ("Operations", "Maintenance", "Engineering", "Safety", "Administration", "IT")
DEMO_POSITIONS = ("Clerk", "Technician", "Engineer", "Senior Engineer", "Safety Officer", "Department Manager", "Administrator")
PERMISSION_CODES = (
    "DOCUMENT_VIEW", "DOCUMENT_UPLOAD", "DOCUMENT_DELETE", "DOCUMENT_DOWNLOAD", "RAG_QUERY", "RAG_SENSITIVE_QUERY",
    "REPORT_VIEW", "REPORT_CREATE", "REPORT_EXPORT", "VISION_ANALYSIS", "CODE_GENERATE",
    "CODE_EXECUTE", "SANDBOX_EXECUTE", "AUDIT_VIEW", "USER_VIEW", "USER_CREATE", "USER_UPDATE",
    "USER_DISABLE", "DEPARTMENT_MANAGE", "POSITION_MANAGE", "PERMISSION_MANAGE", "SECURITY_VIEW",
    "SECURITY_MANAGE", "SYSTEM_ADMIN",
)

DEMO_POSITION_PERMISSIONS = {
    "Clerk": ("DOCUMENT_VIEW", "RAG_QUERY", "REPORT_VIEW"),
    "Technician": ("DOCUMENT_VIEW", "DOCUMENT_DOWNLOAD", "RAG_QUERY", "REPORT_VIEW", "VISION_ANALYSIS"),
    "Engineer": (
        "DOCUMENT_VIEW", "DOCUMENT_DOWNLOAD", "RAG_QUERY", "RAG_SENSITIVE_QUERY", "REPORT_VIEW",
        "REPORT_CREATE", "CODE_GENERATE", "SANDBOX_EXECUTE", "VISION_ANALYSIS",
    ),
    "Safety Officer": (
        "DOCUMENT_VIEW", "DOCUMENT_DOWNLOAD", "RAG_QUERY", "RAG_SENSITIVE_QUERY", "REPORT_VIEW",
        "REPORT_CREATE", "REPORT_EXPORT", "VISION_ANALYSIS", "AUDIT_VIEW",
    ),
    "Department Manager": ("DOCUMENT_VIEW", "DOCUMENT_DOWNLOAD", "RAG_QUERY", "REPORT_VIEW", "REPORT_CREATE", "USER_VIEW"),
    "Administrator": (
        "DOCUMENT_VIEW", "DOCUMENT_UPLOAD", "DOCUMENT_DELETE", "DOCUMENT_DOWNLOAD", "RAG_QUERY",
        "REPORT_VIEW", "REPORT_CREATE", "REPORT_EXPORT", "AUDIT_VIEW", "USER_VIEW", "USER_CREATE",
        "USER_UPDATE", "USER_DISABLE", "DEPARTMENT_MANAGE", "POSITION_MANAGE", "PERMISSION_MANAGE",
        "SECURITY_VIEW", "SECURITY_MANAGE",
    ),
}


def seed_demo_data(db: Session, demo_password: str | None = None) -> None:
    """Insert representative VaultAI demo data without claiming an official hierarchy."""
    for name in DEMO_DEPARTMENTS:
        if db.scalar(select(Department).where(Department.name == name)) is None:
            db.add(Department(name=name, description="VaultAI demo department; not an official MRPL hierarchy."))
    for name in DEMO_POSITIONS:
        if db.scalar(select(Position).where(Position.name == name)) is None:
            db.add(Position(name=name, description="VaultAI demo position; not an official MRPL hierarchy."))
    for code in PERMISSION_CODES:
        if db.scalar(select(Permission).where(Permission.code == code)) is None:
            db.add(Permission(code=code, name=code.replace("_", " ").title(), description="VaultAI demo permission."))
    db.commit()
    positions = {position.name: position for position in db.scalars(select(Position)).all()}
    permissions = {permission.code: permission for permission in db.scalars(select(Permission)).all()}
    for position_name, permission_codes in DEMO_POSITION_PERMISSIONS.items():
        position = positions[position_name]
        for permission_code in permission_codes:
            permission = permissions[permission_code]
            existing = db.scalar(
                select(PositionPermission).where(
                    PositionPermission.position_id == position.id,
                    PositionPermission.permission_id == permission.id,
                )
            )
            if existing is None:
                db.add(PositionPermission(position=position, permission=permission, allowed=True))
    db.commit()
    if demo_password:
        department = db.scalar(select(Department).where(Department.name == "Administration"))
        position = db.scalar(select(Position).where(Position.name == "Clerk"))
        demo_users = (
            ("DEMO001", "Demo Clerk", department, position),
            ("DEMO002", "Demo Engineer", db.scalar(select(Department).where(Department.name == "Engineering")),
             db.scalar(select(Position).where(Position.name == "Engineer"))),
            ("DEMO003", "Demo Safety", db.scalar(select(Department).where(Department.name == "Safety")),
             db.scalar(select(Position).where(Position.name == "Safety Officer"))),
            ("DEMO004", "Demo Admin", department, db.scalar(select(Position).where(Position.name == "Administrator"))),
        )
        for employee_id, full_name, user_department, user_position in demo_users:
            if db.scalar(select(Employee).where(Employee.employee_id == employee_id)) is None:
                db.add(Employee(employee_id=employee_id, full_name=full_name, password_hash=hash_password(demo_password),
                                department=user_department, position=user_position))
        db.commit()


if __name__ == "__main__":
    from backend.app.db.session import SessionLocal

    with SessionLocal() as session:
        seed_demo_data(session, os.environ.get("VAULTAI_DEMO_PASSWORD"))
