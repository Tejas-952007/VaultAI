from typing import List, Dict, Any, Optional
from backend.app.rag.vector_store import vector_store
from backend.app.config import settings


class DocumentSelector:
    def __init__(self, min_similarity_threshold: Optional[float] = None):
        self.min_similarity_threshold = min_similarity_threshold or settings.SIMILARITY_THRESHOLD

    def select_documents(
        self,
        question: str,
        available_documents: List[Dict[str, Any]],
        target_document_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Determine which documents are relevant to the user query BEFORE retrieval.
        Returns a list of selected document_ids.
        """
        ready_doc_ids = [d["id"] for d in available_documents if d.get("status") == "ready"]
        if not ready_doc_ids:
            return []

        # If user explicitly specified target document IDs, restrict selection to those that are ready
        if target_document_ids:
            specified_ready = [did for did in target_document_ids if did in ready_doc_ids]
            return specified_ready

        # Otherwise perform semantic query across all ready documents to select relevant documents
        query_results = vector_store.query(
            query_text=question,
            document_ids=ready_doc_ids,
            top_k=10
        )

        selected_doc_scores: Dict[str, float] = {}
        for r in query_results:
            doc_id = r["document_id"]
            score = r["score"]
            if score > selected_doc_scores.get(doc_id, 0.0):
                selected_doc_scores[doc_id] = score

        # Select documents whose max chunk score meets threshold
        selected_ids = [
            doc_id for doc_id, score in selected_doc_scores.items()
            if score >= self.min_similarity_threshold
        ]

        # Rank selected document IDs by top score descending
        selected_ids.sort(key=lambda did: selected_doc_scores[did], reverse=True)

        return selected_ids


document_selector = DocumentSelector()
