import pytest
from backend.app.rag.vector_store import VectorStoreManager


def test_vector_store_embedding_shape(tmp_path, monkeypatch):
    # Set temporary path for testing vector store
    from backend.app.config import settings
    monkeypatch.setattr(settings, "CHROMA_PATH", tmp_path / "chroma")
    monkeypatch.setattr(settings, "CHROMA_COLLECTION", "test_collection")

    vm = VectorStoreManager()
    embeddings = vm.embed_texts(["Hello world", "VaultAI RAG testing"])
    assert len(embeddings) == 2
    # all-MiniLM-L6-v2 produces 384-dimensional embeddings
    assert len(embeddings[0]) == 384


def test_vector_store_add_and_query(tmp_path, monkeypatch):
    from backend.app.config import settings
    monkeypatch.setattr(settings, "CHROMA_PATH", tmp_path / "chroma_test")
    monkeypatch.setattr(settings, "CHROMA_COLLECTION", "test_collection_query")

    vm = VectorStoreManager()
    chunk_ids = ["doc1_c1", "doc2_c1"]
    texts = ["Refinery safety rules and equipment inspection", "Python coding guidelines for backend"]
    metadatas = [
        {"document_id": "doc1", "source": "safety.pdf", "chunk_id": "doc1_c1"},
        {"document_id": "doc2", "source": "coding.pdf", "chunk_id": "doc2_c1"}
    ]

    vm.add_chunks(chunk_ids, texts, metadatas)

    results = vm.query("What are safety rules?", document_ids=["doc1"], top_k=2)
    assert len(results) == 1
    assert results[0]["document_id"] == "doc1"
    assert results[0]["source"] == "safety.pdf"
