import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from backend.app.config import settings


class AuditLogger:
    def __init__(self, log_file_path: Optional[Path] = None):
        self.log_file_path = log_file_path or settings.AUDIT_LOG_PATH
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): AuditLogger._sanitize_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [AuditLogger._sanitize_value(v) for v in value]
        if isinstance(value, tuple):
            return [AuditLogger._sanitize_value(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            if isinstance(value, str):
                if any(key in value.lower() for key in ["token", "secret", "password", "api_key", "authorization", "bearer"]):
                    return "[redacted]"
                if len(value) > 200:
                    return value[:200] + "..."
            return value
        return str(value)

    def log(
        self,
        event_type: str,
        actor: str = "system",
        resource_id: Optional[str] = None,
        status: str = "info",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Record a minimal audit event to the local JSONL log without storing sensitive payloads."""
        safe_details = self._sanitize_value(details or {})
        if "message" in safe_details and isinstance(safe_details["message"], str):
            safe_details["message_preview"] = safe_details["message"][:160]
            safe_details["message"] = "[redacted]"
        if "image_path" in safe_details and isinstance(safe_details["image_path"], str):
            safe_details["image_path"] = Path(safe_details["image_path"]).name
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "actor": actor,
            "resource_id": resource_id,
            "status": status,
            "details": safe_details
        }

        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=True) + "\n")
        except Exception as e:
            print(f"[AUDIT LOG ERROR] Failed to write audit event: {e}")

        return event


audit_logger = AuditLogger()
