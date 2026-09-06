from pathlib import Path

import pytest

from backend.app.security import (
    APPROVED_MODEL_BY_ROLE,
    resolve_safe_upload_path,
    validate_image_path,
    validate_model_name,
)
from backend.app.config import settings
from backend.app.services.sandbox_service import build_sandbox_command


def test_approved_model_allowed():
    assert validate_model_name("qwen3.5:latest", role="document") == "qwen3.5:latest"
    assert validate_model_name("qwen2.5-coder:7b", role="coding") == "qwen2.5-coder:7b"
    assert validate_model_name("qwen3-vl:8b", role="vision") == "qwen3-vl:8b"


def test_unknown_model_rejected():
    with pytest.raises(ValueError, match="not approved"):
        validate_model_name("gpt-4o-mini", role="document")


def test_cloud_model_rejected():
    with pytest.raises(ValueError, match="not approved"):
        validate_model_name("openai/gpt-4o-mini", role="document")


def test_sandbox_command_includes_hardening():
    cmd = build_sandbox_command("print('hi')")
    assert settings.SANDBOX_IMAGE in cmd
    assert cmd[cmd.index(settings.SANDBOX_IMAGE) + 1] == "-c"
    assert "--network" in cmd
    assert "none" in cmd
    assert "--read-only" in cmd
    assert "--cap-drop" in cmd
    assert "--security-opt" in cmd
    assert "--tmpfs" in cmd


def test_path_traversal_rejected():
    with pytest.raises(ValueError, match="path traversal"):
        resolve_safe_upload_path("../../etc/passwd")


def test_absolute_path_rejected():
    with pytest.raises(ValueError, match="Absolute"):
        validate_image_path("C:/Users/abc/secret.png")


def test_invalid_image_rejected(tmp_path):
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("hello")
    target = tmp_path / "bad.txt"
    with pytest.raises(ValueError, match="Unsupported image format"):
        validate_image_path(str(target), allow_any_extension=False)


def test_upload_size_limit_rejected(tmp_path):
    safe_path = resolve_safe_upload_path("example.pdf", root=tmp_path)
    assert safe_path.parent == tmp_path.resolve()
    assert safe_path.name == "example.pdf"


def test_model_mapping_is_centralized():
    assert APPROVED_MODEL_BY_ROLE["document"] == "qwen3.5:latest"
    assert APPROVED_MODEL_BY_ROLE["coding"] == "qwen2.5-coder:7b"
    assert APPROVED_MODEL_BY_ROLE["vision"] == "qwen3-vl:8b"
