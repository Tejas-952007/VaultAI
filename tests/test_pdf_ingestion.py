import pytest
from pathlib import Path
from backend.app.rag.ingestion import validate_pdf, compute_sha256, chunk_pages, IngestionError


def test_validate_pdf_valid():
    content = b"%PDF-1.4 Fake PDF Content"
    validate_pdf(content, "test.pdf")  # Should not raise


def test_validate_pdf_invalid_extension():
    with pytest.raises(IngestionError, match="Only PDF files are supported"):
        validate_pdf(b"data", "test.txt")


def test_validate_pdf_empty():
    with pytest.raises(IngestionError, match="empty"):
        validate_pdf(b"", "empty.pdf")


def test_compute_sha256():
    content = b"VaultAI Test Document Content"
    hash1 = compute_sha256(content)
    hash2 = compute_sha256(content)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_chunk_pages():
    pages = [
        {"page_number": 1, "text": "This is page one text. " * 30},
        {"page_number": 2, "text": "This is page two text. " * 30}
    ]
    chunks = chunk_pages(pages, chunk_size=200, overlap=50)
    assert len(chunks) > 0
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["chunk_index"] == 1
