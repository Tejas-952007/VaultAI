from unittest.mock import patch
from backend.app.rag.selection import DocumentSelector


def test_document_selector_empty():
    selector = DocumentSelector()
    selected = selector.select_documents(question="Any question?", available_documents=[])
    assert selected == []


def test_document_selector_specified_targets():
    selector = DocumentSelector()
    available = [
        {"id": "doc1", "status": "ready"},
        {"id": "doc2", "status": "ready"},
        {"id": "doc3", "status": "processing"}
    ]
    selected = selector.select_documents(
        question="Query",
        available_documents=available,
        target_document_ids=["doc2", "doc3"]
    )
    # doc3 is not ready, so only doc2 should be selected
    assert selected == ["doc2"]


def test_document_selector_semantic_filter():
    selector = DocumentSelector(min_similarity_threshold=0.3)
    available = [
        {"id": "doc1", "status": "ready"},
        {"id": "doc2", "status": "ready"}
    ]

    mock_query_results = [
        {"document_id": "doc1", "score": 0.85},
        {"document_id": "doc2", "score": 0.15}
    ]

    with patch("backend.app.rag.selection.vector_store.query", return_value=mock_query_results):
        selected = selector.select_documents(question="Safety inspection", available_documents=available)
        assert selected == ["doc1"]
