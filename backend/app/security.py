from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Dict, Optional

from backend.app.config import settings

APPROVED_MODEL_BY_ROLE: Dict[str, str] = {
    "document": "qwen3.5:latest",
    "coding": "qwen2.5-coder:7b",
    "vision": "qwen3-vl:8b",
}

ALLOWED_MODELS = set(APPROVED_MODEL_BY_ROLE.values())
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def validate_model_name(model_name: str, role: Optional[str] = None) -> str:
    """Reject any model not explicitly approved for the local architecture."""
    if not isinstance(model_name, str):
        raise ValueError("Model name must be a string.")

    normalized = model_name.strip()
    if not normalized:
        raise ValueError("Model name is required.")

    lower = normalized.lower()
    if (
        lower.startswith("http://")
        or lower.startswith("https://")
        or "/" in lower
        or lower.startswith("openai")
        or lower.startswith("anthropic")
        or lower.startswith("gemini")
        or lower.startswith("gpt-")
        or lower.startswith("claude")
    ):
        raise ValueError(
            f"Model '{normalized}' is not approved for this local-only deployment."
        )

    allowed = (
        ALLOWED_MODELS
        if role is None
        else {APPROVED_MODEL_BY_ROLE.get(role, normalized)}
    )

    if normalized not in allowed:
        raise ValueError(
            f"Model '{normalized}' is not approved for this local-only deployment."
        )

    return normalized


def resolve_safe_upload_path(
    filename: str,
    root: Optional[Path] = None,
) -> Path:
    """Return a safe file path inside the controlled VaultAI storage directory."""
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename is required.")

    candidate_name = Path(filename).name

    if candidate_name != filename:
        raise ValueError("Unsafe filename: path traversal is not allowed.")

    pure = PurePosixPath(filename)

    if pure.is_absolute() or ".." in pure.parts or filename.startswith(("/", "\\")):
        raise ValueError("Unsafe filename: path traversal is not allowed.")

    storage_root = (root or settings.DOC_STORE_PATH).resolve()
    storage_root.mkdir(parents=True, exist_ok=True)

    final_path = (storage_root / candidate_name).resolve()

    if storage_root not in final_path.parents and final_path != storage_root:
        raise ValueError(
            "Unsafe filename: resolved path escapes the storage directory."
        )

    return final_path


def validate_image_path(
    image_path: str,
    allow_any_extension: bool = False,
    root: Optional[Path] = None,
) -> Path:
    """Validate a user-supplied image path against the local workspace boundary."""
    if not image_path or not isinstance(image_path, str):
        raise ValueError("Image path is required.")

    candidate = Path(image_path)

    # Detect Windows absolute paths even when VaultAI is running on Linux.
    is_windows_absolute = (
        len(image_path) >= 3
        and image_path[0].isalpha()
        and image_path[1] == ":"
        and image_path[2] in ("\\", "/")
    )

    if candidate.is_absolute() or is_windows_absolute:
        # Check the extension first so invalid file types receive the
        # expected validation error even when supplied as an absolute path.
        if not allow_any_extension:
            ext = candidate.suffix.lower()

            if ext not in SUPPORTED_IMAGE_EXTENSIONS:
                raise ValueError(
                    f"Unsupported image format {ext}. "
                    f"Supported: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}"
                )

        raise ValueError("Absolute paths are not allowed for uploaded images.")

    # Prevent path traversal such as ../secret.png
    if ".." in PurePosixPath(image_path).parts:
        raise ValueError("Path traversal is not allowed for uploaded images.")

    workspace_root = (root or Path.cwd()).resolve()
    resolved = (workspace_root / image_path).resolve()

    # Ensure the resolved path remains inside the allowed workspace.
    if workspace_root not in resolved.parents and resolved != workspace_root:
        raise ValueError("Image path is outside the allowed workspace.")

    # File must exist and be a regular file.
    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"Image file not found: {image_path}")

    # Validate supported image format.
    if not allow_any_extension:
        ext = resolved.suffix.lower()

        if ext not in SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError(
                f"Unsupported image format {ext}. "
                f"Supported: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}"
            )

    return resolved