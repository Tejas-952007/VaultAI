from unittest.mock import patch
from backend.app.rag.retrieval import Retriever


def test_retriever_source_constrained():
    retriever = Retriever()

    raw_results = [
        {
            "chunk_id": "doc1_c1",
            "document_id": "doc1",
            "source": "manual.pdf",
            "text": "Safety procedures for equipment maintenance.",
            "score": 0.88,
            "metadata": {}
        }
    ]

    with patch("backend.app.rag.retrieval.vector_store.query", return_value=raw_results) as mock_query:
        evidence = retriever.retrieve("safety procedures", selected_document_ids=["doc1"])
        
        mock_query.assert_called_once_with(
            query_text="safety procedures",
            document_ids=["doc1"],
            top_k=5
        )
        assert len(evidence) == 1
        assert evidence[0].document_id == "doc1"
        assert evidence[0].source == "manual.pdf"
        assert evidence[0].score == 0.88
