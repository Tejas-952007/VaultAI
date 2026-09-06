from unittest.mock import patch


def test_list_documents_requires_authentication(client):
    response = client.get("/api/v1/documents")
    assert response.status_code == 401


def test_list_documents_empty(authenticated_client):
    response = authenticated_client.get("/api/v1/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_authenticated_employee_without_permission_is_forbidden(permissionless_client):
    response = permissionless_client.get("/api/v1/documents")
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions."


def test_upload_invalid_file_type(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", b"plain text", "text/plain")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"]["code"] == "INGESTION_ERROR"


def test_upload_valid_pdf_mocked(authenticated_client, tmp_path, monkeypatch):
    from backend.app.config import settings
    monkeypatch.setattr(settings, "DOC_STORE_PATH", tmp_path / "docs")
    monkeypatch.setattr(settings, "CHROMA_PATH", tmp_path / "chroma")

    fake_doc = {
        "id": "doc123",
        "filename": "sample.pdf",
        "sha256": "fakehash123",
        "size_bytes": 100,
        "status": "ready",
        "chunks_count": 2
    }

    with patch("backend.app.routes.documents.ingest_pdf", return_value=fake_doc):
        response = authenticated_client.post(
            "/api/v1/documents",
            files={"file": ("sample.pdf", b"%PDF-1.4 sample content", "application/pdf")}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "doc123"
        assert data["status"] == "ready"
