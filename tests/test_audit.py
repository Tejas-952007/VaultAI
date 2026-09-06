import json
from pathlib import Path
from backend.app.audit.audit import AuditLogger


def test_audit_logger(tmp_path):
    log_file = tmp_path / "audit.log"
    logger = AuditLogger(log_file_path=log_file)

    event = logger.log(
        event_type="test_event",
        actor="unit_test",
        resource_id="res_123",
        status="success",
        details={"key": "value"}
    )

    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    
    parsed = json.loads(lines[0])
    assert parsed["event_type"] == "test_event"
    assert parsed["actor"] == "unit_test"
    assert parsed["resource_id"] == "res_123"
    assert parsed["details"]["key"] == "value"
