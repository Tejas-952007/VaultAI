from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    ollama_status: str = "unknown"
    ollama_model: str = ""
    available_models: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(..., description="User query or input message")
    document_ids: Optional[List[str]] = Field(default_factory=list, description="Optional list of target document IDs")
    system_prompt: Optional[str] = Field(default=None, description="Optional custom system prompt override")
    image_path: Optional[str] = Field(default=None, description="Optional path to a local image file for vision analysis")


class EvidenceItem(BaseModel):
    document_id: str
    source: str
    chunk_id: str
    score: float
    snippet: str


class ChatResponse(BaseModel):
    request_id: str
    answer: str
    route: str = "chat"
    model: str
    duration_ms: float
    evidence: List[EvidenceItem] = Field(default_factory=list)
    status: str = "success"
    # Coding Agent Extensions
    generated_code: Optional[str] = None
    sandbox_result: Optional[Dict[str, Any]] = None
    coding_attempts: Optional[int] = None
    coding_status: Optional[str] = None
    coding_error: Optional[str] = None
    # Vision Agent Extensions
    vision_status: Optional[str] = None
    vision_result: Optional[Dict[str, Any]] = None
    vision_error: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    request_id: Optional[str] = None
    status: str = "error"
    error: ErrorDetail
