from typing import TypedDict, List, Dict, Any, Optional
from backend.app.schemas import EvidenceItem


class VaultAIState(TypedDict, total=False):
    request_id: str
    message: str
    document_ids: Optional[List[str]]
    route: str
    selected_documents: List[str]
    evidence: List[EvidenceItem]
    model: str
    duration_ms: float
    answer: str
    status: str
    error: Optional[str]
    tool_results: List[Dict[str, Any]]
    artifacts: List[Dict[str, Any]]
    # Coding Agent State
    generated_code: Optional[str]
    sandbox_result: Optional[Dict[str, Any]]
    coding_attempts: int
    coding_status: Optional[str]
    coding_error: Optional[str]
    # Vision Agent State
    image_path: Optional[str]
    vision_status: Optional[str]
    vision_result: Optional[Dict[str, Any]]
    vision_error: Optional[str]
