from backend.app.graph.state import VaultAIState
from backend.app.services.document_store import document_store
from backend.app.services.grounded_generation import grounded_generator, INSUFFICIENT_MESSAGE
from backend.app.services.ollama_service import ollama_service
from backend.app.rag.selection import document_selector
from backend.app.rag.retrieval import retriever
from backend.app.audit.audit import audit_logger


def document_agent_node(state: VaultAIState) -> VaultAIState:
    """Document agent node executing source-constrained RAG."""
    request_id = state.get("request_id")
    message = state.get("message", "")
    req_doc_ids = state.get("document_ids")

    audit_logger.log(
        event_type="agent_execution",
        resource_id=request_id,
        details={"agent": "document_agent", "message": message}
    )

    available_docs = document_store.list_documents(ready_only=True)

    if not available_docs:
        audit_logger.log(
            event_type="chat_response_abstain",
            resource_id=request_id,
            status="insufficient",
            details={"reason": "No uploaded documents available."}
        )
        state["answer"] = INSUFFICIENT_MESSAGE
        state["model"] = ollama_service.default_model
        state["duration_ms"] = 0.0
        state["evidence"] = []
        state["selected_documents"] = []
        state["status"] = "insufficient"
        return state

    selected_doc_ids = document_selector.select_documents(
        question=message,
        available_documents=available_docs,
        target_document_ids=req_doc_ids
    )
    state["selected_documents"] = selected_doc_ids

    if not selected_doc_ids:
        audit_logger.log(
            event_type="chat_response_abstain",
            resource_id=request_id,
            status="insufficient",
            details={"reason": "No relevant documents selected for query."}
        )
        state["answer"] = INSUFFICIENT_MESSAGE
        state["model"] = ollama_service.default_model
        state["duration_ms"] = 0.0
        state["evidence"] = []
        state["status"] = "insufficient"
        return state

    evidence = retriever.retrieve(
        question=message,
        selected_document_ids=selected_doc_ids
    )
    state["evidence"] = evidence

    top_score = max([e.score for e in evidence]) if evidence else 0.0
    if not evidence or top_score < 0.20:
        audit_logger.log(
            event_type="chat_response_abstain",
            resource_id=request_id,
            status="insufficient",
            details={"top_score": top_score, "selected_docs": selected_doc_ids}
        )
        state["answer"] = INSUFFICIENT_MESSAGE
        state["model"] = ollama_service.default_model
        state["duration_ms"] = 0.0
        state["status"] = "insufficient"
        return state

    answer, model_used, duration_ms, status_str = grounded_generator.generate(
        question=message,
        evidence=evidence
    )

    state["answer"] = answer
    state["model"] = model_used
    state["duration_ms"] = duration_ms
    state["status"] = status_str

    audit_logger.log(
        event_type="chat_response_success" if status_str == "success" else "chat_response_abstain",
        resource_id=request_id,
        status=status_str,
        details={
            "model": model_used,
            "duration_ms": duration_ms,
            "evidence_count": len(evidence),
            "selected_docs": selected_doc_ids
        }
    )

    return state
