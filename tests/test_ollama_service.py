import pytest
import httpx
from unittest.mock import patch, MagicMock
from backend.app.services.ollama_service import OllamaService, OllamaServiceError


def test_ollama_service_health_available():
    service = OllamaService(base_url="http://localhost:11434")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": [{"name": "qwen3.5:latest"}]}

    with patch.object(httpx.Client, "get", return_value=mock_response):
        health = service.check_health()
        assert health["available"] is True
        assert "qwen3.5:latest" in health["models"]


def test_ollama_service_health_unavailable():
    service = OllamaService(base_url="http://localhost:11434")

    with patch.object(httpx.Client, "get", side_effect=httpx.ConnectError("Connection refused")):
        health = service.check_health()
        assert health["available"] is False
        assert "Could not connect" in health["error"]


def test_ollama_service_generate_success():
    service = OllamaService(base_url="http://localhost:11434", default_model="qwen3.5:latest")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": "VaultAI test answer",
        "model": "qwen3.5:latest",
        "total_duration": 500000000  # 500ms
    }

    with patch.object(httpx.Client, "post", return_value=mock_response):
        result = service.generate(prompt="What is VaultAI?")
        assert result["status"] == "success"
        assert result["text"] == "VaultAI test answer"
        assert result["model"] == "qwen3.5:latest"
        assert result["duration_ms"] == 500.0


def test_ollama_service_generate_connection_failure():
    service = OllamaService(base_url="http://localhost:11434")

    with patch.object(httpx.Client, "post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(OllamaServiceError) as exc_info:
            service.generate(prompt="Hello")
        assert exc_info.value.code == "MODEL_UNAVAILABLE"


def test_ollama_service_generate_timeout():
    service = OllamaService(base_url="http://localhost:11434")

    with patch.object(httpx.Client, "post", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(OllamaServiceError) as exc_info:
            service.generate(prompt="Hello")
        assert exc_info.value.code == "MODEL_TIMEOUT"
