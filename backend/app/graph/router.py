from backend.app.graph.state import VaultAIState
from backend.app.audit.audit import audit_logger


DOCUMENT_KEYWORDS = [
    "document", "report", "sop", "manual", "uploaded file",
    "according to the document", "what does the report say",
    "based on the documents", "pdf", "file"
]

CODING_KEYWORDS = [
    "code", "python", "javascript", "function", "script",
    "debug", "programming", "class", "def ", "import "
]

VISION_KEYWORDS = [
    "image", "photo", "diagram", "visual", "inspect image",
    "picture", "chart", "figure"
]


def classify_route(message: str, document_ids: float = None) -> str:
    """Deterministic keyword/rule classifier."""
    msg_lower = message.lower()

    # Explicit document ID parameter targets document RAG
    if document_ids:
        return "document"

    # Check vision keywords first
    for kw in VISION_KEYWORDS:
        if kw in msg_lower:
            return "vision"

    # Check coding keywords
    for kw in CODING_KEYWORDS:
        if kw in msg_lower:
            return "coding"

    # Check document keywords
    for kw in DOCUMENT_KEYWORDS:
        if kw in msg_lower:
            return "document"

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
