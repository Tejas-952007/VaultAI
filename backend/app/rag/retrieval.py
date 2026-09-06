from typing import List
from backend.app.schemas import EvidenceItem
from backend.app.rag.vector_store import vector_store
from backend.app.config import settings


class Retriever:
    def retrieve(
        self,
        question: str,
        selected_document_ids: List[str],
        top_k: int = settings.RETRIEVAL_TOP_K
    ) -> List[EvidenceItem]:
        """
        Retrieve relevant evidence chunks strictly constrained to selected_document_ids.
        """
        if not selected_document_ids:
            return []

        raw_results = vector_store.query(
            query_text=question,
            document_ids=selected_document_ids,
            top_k=top_k
        )

        evidence_items = []
        for r in raw_results:
            evidence_items.append(
                EvidenceItem(
                    document_id=r["document_id"],
                    source=r["source"],
                    chunk_id=r["chunk_id"],
                    score=r["score"],
                    snippet=r["text"]
                )
            )

        return evidence_items


retriever = Retriever()
