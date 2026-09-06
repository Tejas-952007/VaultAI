from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.app.routes.sandbox import SandboxExecuteRequest, sandbox_execute
from backend.app.services.sandbox_service import SandboxResult


@pytest.mark.asyncio
async def test_sandbox_execution_records_postgres_and_legacy_audit():
    db = SimpleNamespace(commit=Mock(), rollback=Mock())
    employee = SimpleNamespace(id=7)
    result = SandboxResult(stdout="4", stderr="", exit_code=0, duration=0.1, timed_out=False)

    with patch("backend.app.routes.sandbox.execute_code", new=AsyncMock(return_value=result)), \
         patch("backend.app.routes.sandbox.record_sandbox_audit", new=AsyncMock()) as legacy_audit, \
         patch("backend.app.routes.sandbox.record_event") as postgres_audit:
        response = await sandbox_execute(
            SandboxExecuteRequest(language="python", code="print(2+2)"),
            employee=employee,
            db=db,
        )

    assert response.exit_code == 0
    legacy_audit.assert_awaited_once()
    postgres_audit.assert_called_once()
    details = postgres_audit.call_args.kwargs["details"]
    assert details["exit_code"] == 0
    assert "code" not in details
    assert "stdout" not in details
    db.commit.assert_called_once()
