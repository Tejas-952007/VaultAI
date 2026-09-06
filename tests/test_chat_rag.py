from unittest.mock import patch
from backend.app.schemas import EvidenceItem


def test_chat_rag_no_docs_abstains(authenticated_client):
    with patch("backend.app.graph.nodes.document_agent.document_store.list_documents", return_value=[]):
        response = authenticated_client.post(
            "/api/v1/chat",
            json={"message": "What is the pressure limit?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "insufficient"
        assert "not have enough information" in data["answer"]


def test_chat_rag_success_flow(authenticated_client):
    mock_docs = [{"id": "doc1", "status": "ready"}]
    mock_evidence = [
        EvidenceItem(
            document_id="doc1",
            source="manual.pdf",
            chunk_id="doc1_c1",
            score=0.88,
            snippet="Maximum operating temperature is 450C."
        )
    ]

    with patch("backend.app.graph.nodes.document_agent.document_store.list_documents", return_value=mock_docs):
        with patch("backend.app.graph.nodes.document_agent.document_selector.select_documents", return_value=["doc1"]):
            with patch("backend.app.graph.nodes.document_agent.retriever.retrieve", return_value=mock_evidence):
                with patch("backend.app.graph.nodes.document_agent.grounded_generator.generate", return_value=(
                    "The maximum operating temperature is 450C according to manual.pdf.",
                    "qwen3.5:latest",
                    350.0,
                    "success"
                )):
                    response = authenticated_client.post(
                        "/api/v1/chat",
                        json={"message": "What is the maximum operating temperature?"}
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "success"
                    assert "450C" in data["answer"]
                    assert data["model"] == "qwen3.5:latest"
                    assert len(data["evidence"]) == 1
                    assert data["evidence"][0]["document_id"] == "doc1"
