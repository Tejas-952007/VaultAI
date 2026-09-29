from backend.app.graph.state import VaultAIState
from backend.app.audit.audit import audit_logger


import re

ENGINEERING_DOCUMENT_PHRASES = [
    "specification code", "product designation", "pipeline code",
    "drawing", "drawings", "p&id", "pid", "process flow", "insulation class",
    "pressure class", "hazard class", "designation code", "engineering report",
    "reactor", "refinery", "instrument air", "standard operating procedure",
]

DOCUMENT_KEYWORDS = [
    "document", "report", "sop", "manual", "uploaded file",
    "according to the document", "what does the report say",
    "based on the documents", "pdf", "file"
]

VISION_KEYWORDS = [
    "image", "photo", "inspect image", "picture", "figure", "visual"
]


def classify_route(message: str, document_ids: list | None = None) -> str:
    """Deterministic keyword/rule classifier."""
    msg_lower = message.lower()

    # Explicit document ID parameter targets document RAG
    if document_ids:
        return "document"

    # Engineering document domain terms always belong to document RAG
    for phrase in ENGINEERING_DOCUMENT_PHRASES:
        if phrase in msg_lower:
            return "document"

    # Check vision keywords
    for kw in VISION_KEYWORDS:
        if kw in msg_lower:
            return "vision"

    # Check document keywords
    for kw in DOCUMENT_KEYWORDS:
        if kw in msg_lower:
            return "document"

    # Check coding patterns (prevent false positives on technical codes/classes)
    if any(k in msg_lower for k in ["python", "javascript", "typescript", "debug", "programming", "def ", "import "]):
        return "coding"
    if re.search(r"\b(?:write|generate|execute|run|debug)\s+(?:a\s+)?(?:code|function|script|class)\b", msg_lower):
        return "coding"
    if re.search(r"\bclass\s+in\s+programming\b", msg_lower):
        return "coding"
    if re.search(r"\bfunction\b", msg_lower) and any(w in msg_lower for w in ["write", "compute", "calculate", "return"]):
        return "coding"
    if re.search(r"\bscript\b", msg_lower):
        return "coding"

    # Default fallback to document RAG
    return "document"


def router_node(state: VaultAIState) -> VaultAIState:
    """LangGraph router node that decides agent target."""
    message = state.get("message", "")
    doc_ids = state.get("document_ids")
    
    route = classify_route(message=message, document_ids=doc_ids)
    state["route"] = route

    audit_logger.log(
        event_type="selected_route",
        resource_id=state.get("request_id"),
        details={"route": route, "message": message}
    )

    return state


def route_decision(state: VaultAIState) -> str:
    """Conditional edge router function for LangGraph."""
    return state.get("route", "document")
