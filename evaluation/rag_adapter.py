"""Read-only adapter over the existing VaultAI RAG pipeline.

This module imports production services. It must not mutate application
configuration, collections, or documents.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from backend.app.config import settings
from backend.app.rag.retrieval import retriever
from backend.app.schemas import ChatRequest, EvidenceItem
from backend.app.services.chat_service import chat_service
from backend.app.services.document_store import document_store


async def run_existing_rag(question: str) -> Dict[str, Any]:
    """Execute one query through the production LangGraph chat pipeline.

    Retrieval Top-K is whatever the live Retriever uses (settings.RETRIEVAL_TOP_K,
    currently 5). Generation uses grounded_generator + Ollama.
    """
    ready_docs = document_store.list_documents(ready_only=True)
    ready_ids = [d["id"] for d in ready_docs]

    start = time.perf_counter()
    response = await chat_service.handle_chat(
        ChatRequest(message=question, document_ids=[]),
        employee_position="Engineer",
    )
    latency_s = time.perf_counter() - start

    evidence: List[EvidenceItem] = list(response.evidence or [])
    # Same Retriever class and Top-K as production, queried across ready
    # documents so Recall@5 always has a 5-hit window when the collection allows.
    topk_evidence = retriever.retrieve(
        question=question,
        selected_document_ids=ready_ids,
        top_k=settings.RETRIEVAL_TOP_K,
    ) if ready_ids else evidence[: settings.RETRIEVAL_TOP_K]

    pipeline_chunks = [
        {
            "chunk_id": item.chunk_id,
            "document_id": item.document_id,
            "source": item.source,
            "score": item.score,
            "snippet": item.snippet,
        }
        for item in evidence
    ]
    topk_chunks = [
        {
            "chunk_id": item.chunk_id,
            "document_id": item.document_id,
            "source": item.source,
            "score": item.score,
            "snippet": item.snippet,
        }
        for item in topk_evidence[: settings.RETRIEVAL_TOP_K]
    ]

    return {
        "request_id": response.request_id,
        "question": question,
        "answer": response.answer,
        "status": response.status,
        "route": response.route,
        "model": response.model,
        "pipeline_duration_ms": response.duration_ms,
        "latency_seconds": round(latency_s, 4),
        "pipeline_evidence": pipeline_chunks,
        "top5_chunks": topk_chunks,
        "retrieved_chunk_ids": [c["chunk_id"] for c in topk_chunks],
        "retrieved_document_ids": sorted({c["document_id"] for c in topk_chunks}),
        "context": "\n\n".join(c["snippet"] for c in topk_chunks),
        "ready_document_ids": ready_ids,
        "retrieval_top_k": settings.RETRIEVAL_TOP_K,
    }
