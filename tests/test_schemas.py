import pytest
from pydantic import ValidationError
from backend.app.schemas import ChatRequest, ChatResponse, HealthResponse, ErrorResponse


def test_chat_request_valid():
    req = ChatRequest(message="Hello VaultAI")
    assert req.message == "Hello VaultAI"
    assert req.document_ids == []
    assert req.system_prompt is None


def test_chat_request_missing_message():
    with pytest.raises(ValidationError):
        ChatRequest()  # type: ignore


def test_chat_response_schema():
    res = ChatResponse(
        request_id="test-uuid",
        answer="Test response",
        model="qwen3.5:latest",
        duration_ms=150.5
    )
    assert res.request_id == "test-uuid"
    assert res.status == "success"
    assert res.duration_ms == 150.5
    assert res.evidence == []
