from unittest.mock import patch
from backend.app.schemas import EvidenceItem
from backend.app.services.ollama_service import OllamaServiceError


def test_post_chat_success(authenticated_client):
    mock_docs = [{"id": "doc1", "status": "ready"}]
    mock_evidence = [
        EvidenceItem(
            document_id="doc1",
            source="test.pdf",
            chunk_id="doc1_c1",
            score=0.85,
            snippet="Hello! I am VaultAI running on local Qwen3.5."
        )
    ]
    with patch("backend.app.graph.nodes.document_agent.document_store.list_documents", return_value=mock_docs):
        with patch("backend.app.graph.nodes.document_agent.document_selector.select_documents", return_value=["doc1"]):
            with patch("backend.app.graph.nodes.document_agent.retriever.retrieve", return_value=mock_evidence):
                with patch("backend.app.graph.nodes.document_agent.grounded_generator.generate", return_value=(
                    "Hello! I am VaultAI running on local Qwen3.5.",
                    "qwen3.5:latest",
                    320.0,
                    "success"
                )):
                    response = authenticated_client.post(
                        "/api/v1/chat",
                        json={"message": "Hello VaultAI"}
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "success"
                    assert data["answer"] == "Hello! I am VaultAI running on local Qwen3.5."
                    assert data["model"] == "qwen3.5:latest"
                    assert data["duration_ms"] == 320.0
                    assert "request_id" in data


def test_post_chat_ollama_unavailable(authenticated_client):
    mock_docs = [{"id": "doc1", "status": "ready"}]
    mock_evidence = [
        EvidenceItem(
            document_id="doc1",
            source="test.pdf",
            chunk_id="doc1_c1",
            score=0.85,
            snippet="Some context"
        )
    ]
    with patch("backend.app.graph.nodes.document_agent.document_store.list_documents", return_value=mock_docs):
        with patch("backend.app.graph.nodes.document_agent.document_selector.select_documents", return_value=["doc1"]):
            with patch("backend.app.graph.nodes.document_agent.retriever.retrieve", return_value=mock_evidence):
                with patch(
                    "backend.app.graph.nodes.document_agent.grounded_generator.generate",
                    side_effect=OllamaServiceError("MODEL_UNAVAILABLE", "Local Ollama service is unavailable.")
                ):
                    response = authenticated_client.post(
                        "/api/v1/chat",
                        json={"message": "Hello VaultAI"}
                    )
                    assert response.status_code == 503
                    data = response.json()
                    assert data["detail"]["status"] == "error"
                    assert data["detail"]["error"]["code"] == "MODEL_UNAVAILABLE"
