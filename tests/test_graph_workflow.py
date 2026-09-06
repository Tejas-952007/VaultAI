from unittest.mock import patch, AsyncMock
from backend.app.schemas import EvidenceItem
from backend.app.graph.workflow import vaultai_graph_app


def test_workflow_coding_route(authenticated_client):
    with patch("backend.app.graph.nodes.coding_agent.ollama_service.check_health", return_value={"available": True, "models": ["qwen2.5-coder:7b"]}):
        with patch("backend.app.graph.nodes.coding_agent.ollama_service.generate", return_value={"text": "print('hello')", "model": "qwen2.5-coder:7b", "duration_ms": 100.0, "status": "success"}):
            with patch("backend.app.graph.nodes.coding_agent.execute_code", new_callable=AsyncMock) as mock_exec:
                from backend.app.services.sandbox_service import SandboxResult
                mock_exec.return_value = SandboxResult(stdout="hello", stderr="", exit_code=0, duration=0.1, timed_out=False)
                
                response = authenticated_client.post(
                    "/api/v1/chat",
                    json={"message": "Write a python function"}
                )
                assert response.status_code == 200
                data = response.json()
                assert data["route"] == "coding"
                assert data["status"] == "success"
                assert "hello" in data["answer"]


def test_workflow_vision_route(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/chat",
        json={"message": "Inspect image diagram"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "vision"
    # The vision agent now returns 'error' if no image is provided, 
    # rather than 'not_available' (which is reserved for missing models).
    assert data["status"] in ["not_available", "error"]


def test_workflow_document_route_rag_success(authenticated_client):
    mock_docs = [{"id": "doc1", "status": "ready"}]
    mock_evidence = [
        EvidenceItem(
            document_id="doc1",
            source="manual.pdf",
            chunk_id="doc1_c1",
            score=0.88,
            snippet="Operating limit is 100 BAR."
        )
    ]

    with patch("backend.app.graph.nodes.document_agent.document_store.list_documents", return_value=mock_docs):
        with patch("backend.app.graph.nodes.document_agent.document_selector.select_documents", return_value=["doc1"]):
            with patch("backend.app.graph.nodes.document_agent.retriever.retrieve", return_value=mock_evidence):
                with patch("backend.app.graph.nodes.document_agent.grounded_generator.generate", return_value=(
                    "The operating limit is 100 BAR according to manual.pdf.",
                    "qwen3.5:latest",
                    250.0,
                    "success"
                )):
                    response = authenticated_client.post(
                        "/api/v1/chat",
                        json={"message": "What is the operating limit in the document?"}
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["route"] == "document"
                    assert data["status"] == "success"
                    assert "100 BAR" in data["answer"]
                    assert len(data["evidence"]) == 1
                    assert data["evidence"][0]["document_id"] == "doc1"
