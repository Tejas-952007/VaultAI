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

        # Query candidate pool size: scale with document count to ensure small documents
        # (e.g. 1-page engineering reports) are not crowded out by large manuals
        candidate_k = min(150, max(35, len(ready_doc_ids) * 15))

        query_results = vector_store.query(
            query_text=question,
            document_ids=ready_doc_ids,
            top_k=candidate_k
        )

        selected_doc_scores: Dict[str, float] = {}
        for r in query_results:
            doc_id = r["document_id"]
            score = r["score"]
            if score > selected_doc_scores.get(doc_id, 0.0):
                selected_doc_scores[doc_id] = score

        # Lexical and OKF metadata match: if question explicitly references document filename or concept
        q_lower = question.lower()
        for doc in available_documents:
            doc_id = doc.get("id")
            if not doc_id or doc_id not in ready_doc_ids:
                continue

            fname = doc.get("filename", "").lower()
            fname_stem = fname.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
            okf_concept = (doc.get("okf_concept_id") or "").lower()

            # Meaningful tokens from filename
            tokens = [t for t in fname_stem.split() if len(t) > 3]
            matched_tokens = sum(1 for t in tokens if t in q_lower)

            if (tokens and matched_tokens >= len(tokens) / 2) or (okf_concept and okf_concept in q_lower):
                if doc_id not in selected_doc_scores:
                    direct_hits = vector_store.query(query_text=question, document_ids=[doc_id], top_k=1)
                    if direct_hits:
                        selected_doc_scores[doc_id] = direct_hits[0]["score"]

        # Select documents whose max chunk score meets threshold
        selected_ids = [
            doc_id for doc_id, score in selected_doc_scores.items()
            if score >= self.min_similarity_threshold
        ]

        # Rank selected document IDs by top score descending
        selected_ids.sort(key=lambda did: selected_doc_scores[did], reverse=True)

        return selected_ids


document_selector = DocumentSelector()
