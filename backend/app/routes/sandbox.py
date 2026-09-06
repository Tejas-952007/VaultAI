from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.auth.authorization import require_permission
from backend.app.audit.events import record_event
from backend.app.db.models import Employee
from backend.app.db.session import get_db
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime
from backend.app.services.sandbox_service import execute_code
from backend.app.models.audit import record_sandbox_audit
from backend.app.rate_limit import sandbox_limiter

router = APIRouter()

class SandboxExecuteRequest(BaseModel):
    language: str = Field(..., description="Programming language, currently only 'python' is supported")
    code: str = Field(..., description="Source code to execute")

class SandboxExecuteResponse(BaseModel):
    request_id: str = Field(..., description="Unique identifier for this execution request")
    language: str
    stdout: str = Field(..., description="Standard output from the execution")
    stderr: str = Field(..., description="Standard error from the execution")
    exit_code: int = Field(..., description="Process exit code")
    duration_seconds: float = Field(..., description="Execution duration in seconds")
    timed_out: bool = Field(..., description="True if execution timed out")
    error_message: str | None = Field(None, description="Error message if the sandbox failed to start")

@router.post("/sandbox/execute", response_model=SandboxExecuteResponse)
async def sandbox_execute(
    request: SandboxExecuteRequest,
    employee: Employee = Depends(require_permission("SANDBOX_EXECUTE")),
    db: Session = Depends(get_db),
):
    client_ip = "sandbox:unknown"
    if not sandbox_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail={"status": "error", "error": {"code": "RATE_LIMITED", "message": "Sandbox execution is rate-limited for this prototype."}})

    if request.language.lower() != "python":
        raise HTTPException(status_code=400, detail="Only Python execution is supported in this prototype")
    if len(request.code) > 20000:
        raise HTTPException(status_code=413, detail="Code payload is too large for this prototype sandbox.")
    request_id = str(uuid4())
    start_time = datetime.utcnow()
    try:
        result = await execute_code(request.code)
    except Exception as exc:
        _record_postgres_audit(
            db,
            employee,
            request_id=request_id,
            language=request.language,
            duration_seconds=0.0,
            exit_code=-1,
            timed_out=False,
        )
        # Record audit with failure
        await record_sandbox_audit(
            request_id=request_id,
            language=request.language,
            timestamp=start_time,
            duration_seconds=0.0,
            exit_code=-1,
            timed_out=False,
            error_message=str(exc),
        )
        raise HTTPException(status_code=500, detail="Sandbox execution failed")
    _record_postgres_audit(
        db,
        employee,
        request_id=request_id,
        language=request.language,
        duration_seconds=result.duration,
        exit_code=result.exit_code,
        timed_out=result.timed_out,
    )
    # Record audit
    await record_sandbox_audit(
        request_id=request_id,
        language=request.language,
        timestamp=start_time,
        duration_seconds=result.duration,
        exit_code=result.exit_code,
        timed_out=result.timed_out,
        error_message=result.error_message,
    )
    return SandboxExecuteResponse(
        request_id=request_id,
        language=request.language,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        duration_seconds=result.duration,
        timed_out=result.timed_out,
        error_message=result.error_message,
    )


def _record_postgres_audit(
    db: Session,
    employee: Employee,
    *,
    request_id: str,
    language: str,
    duration_seconds: float,
    exit_code: int,
    timed_out: bool,
) -> None:
    """Persist execution metadata without storing source or command output."""
    record_event(
        db,
        action="SANDBOX_EXECUTION",
        result="TIMEOUT" if timed_out else ("SUCCESS" if exit_code == 0 else "FAILURE"),
        employee=employee,
        resource_type="SANDBOX",
        resource_id=language,
        request_id=request_id,
        details={
            "language": language,
            "duration_seconds": duration_seconds,
            "exit_code": exit_code,
            "timed_out": timed_out,
        },
    )
    db.commit()
