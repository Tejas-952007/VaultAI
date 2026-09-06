from backend.app.graph.state import VaultAIState
from backend.app.services.ollama_service import ollama_service
from backend.app.audit.audit import audit_logger
from backend.app.security import validate_image_path
import base64
import os
from typing import Dict, Any


VISION_MODEL = "qwen3-vl:8b"
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_SIZE_MB = 10


async def vision_agent_node(state: VaultAIState) -> VaultAIState:
    """
    Real async vision agent node.
    Analyzes a local image using the local Ollama vision model (qwen3-vl:8b).
    """
    request_id = state.get("request_id")
    message = state.get("message", "")
    image_path = state.get("image_path")

    audit_logger.log(
        event_type="agent_execution",
        resource_id=request_id,
        details={"agent": "vision_agent", "message": message, "image_path": image_path},
    )

    # 1. Model Availability Check
    health = ollama_service.check_health()
    if not health["available"] or VISION_MODEL not in health.get("models", []):
        state["answer"] = f"Vision model {VISION_MODEL} not available locally. Please run 'ollama pull {VISION_MODEL}'."
        state["model"] = VISION_MODEL
        state["status"] = "not_available"
        state["vision_status"] = "not_available"
        return state

    # 2. Image Validation
    if not image_path:
        state["answer"] = "No image provided for analysis. Please upload an image."
        state["status"] = "error"
        state["vision_status"] = "failed"
        state["vision_error"] = "No image path provided"
        return state

    try:
        image_path = str(validate_image_path(image_path))
    except ValueError as exc:
        state["answer"] = str(exc)
        state["status"] = "error"
        state["vision_status"] = "failed"
        state["vision_error"] = str(exc)
        return state

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in SUPPORTED_IMAGE_EXTENSIONS:
        state["answer"] = f"Unsupported image format {ext}. Supported: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
        state["status"] = "error"
        state["vision_status"] = "failed"
        state["vision_error"] = "Unsupported format"
        return state

    if os.path.getsize(image_path) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        state["answer"] = f"Image file too large. Maximum size is {MAX_IMAGE_SIZE_MB}MB."
        state["status"] = "error"
        state["vision_status"] = "failed"
        state["vision_error"] = "File too large"
        return state

    # 3. Image Processing (Base64 encoding for Ollama)
    try:
        with open(image_path, "rb") as img_file:
            img_bytes = img_file.read()
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    except Exception as exc:
        state["answer"] = f"Failed to read image file: {exc}"
        state["status"] = "error"
        state["vision_status"] = "failed"
        state["vision_error"] = str(exc)
        return state

    # 4. Vision Generation
    try:
        system_prompt = (
            "You are VaultAI's sovereign vision assistant. "
            "Your goal is to analyze the provided image and answer the user's question accurately. "
            "INSTRUCTIONS:\n"
            "1. Describe only visible information. Distinguish visible facts from interpretation.\n"
            "2. If something cannot be determined from the image, state it clearly.\n"
            "3. Do not invent text that cannot be read or claim certainty when the image is ambiguous.\n"
            "4. Be concise and structured in your observations."
        )

        res = ollama_service.generate(
            prompt=message,
            system_prompt=system_prompt,
            model=VISION_MODEL,
            images=[img_base64],
            role="vision",
        )
        
        answer_text = res.get("text", "").strip()
        duration_ms = res.get("duration_ms", 0.0)

        state["answer"] = answer_text
        state["model"] = VISION_MODEL
        state["duration_ms"] = duration_ms
        state["status"] = "success"
        state["vision_status"] = "success"
        state["vision_result"] = {
            "description": answer_text,
            "model": VISION_MODEL,
            "duration_ms": duration_ms
        }
        return state

    except Exception as exc:
        state["answer"] = f"Vision analysis failed: {exc}"
        state["status"] = "error"
        state["vision_status"] = "failed"
        state["vision_error"] = str(exc)
        return state
