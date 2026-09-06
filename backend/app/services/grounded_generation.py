from typing import List, Dict, Any, Tuple
from backend.app.schemas import EvidenceItem
from backend.app.services.ollama_service import ollama_service


INSUFFICIENT_MESSAGE = "I do not have enough information to answer this question based on the provided documents."


class GroundedGenerator:
    def generate(
        self,
        question: str,
        evidence: List[EvidenceItem]
    ) -> Tuple[str, str, float, str]:
        """
        Generate a grounded answer using Ollama service.
        Returns Tuple[answer_text, model_name, duration_ms, status_str].
        """
        if not evidence:
            return INSUFFICIENT_MESSAGE, ollama_service.default_model, 0.0, "insufficient"

        # Format context from evidence snippets
        context_snippets = []
        for i, item in enumerate(evidence, 1):
            context_snippets.append(
                f"[{i}] Document: {item.source} (ID: {item.document_id}, Chunk: {item.chunk_id})\n"
                f"Content: {item.snippet}\n"
            )
        formatted_context = "\n---\n".join(context_snippets)

        system_prompt = (
            "You are VaultAI, a sovereign on-premise AI assistant.\n"
            "INSTRUCTIONS:\n"
            "1. Answer the user's question using ONLY the provided evidence snippets below.\n"
            "2. Do NOT invent facts or use outside knowledge as evidence.\n"
            "3. If the supplied evidence is missing, insufficient, or does not directly answer the question, "
            "you MUST state: 'I do not have enough information to answer this question based on the provided documents.'\n"
            "4. Be accurate, concise, and cite the document source where relevant."
        )

        user_prompt = (
            f"EVIDENCE SNIPPETS:\n"
            f"{formatted_context}\n\n"
            f"QUESTION: {question}\n\n"
            f"ANSWER:"
        )

        res = ollama_service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            options={
                "num_predict": 256,
                "temperature": 0.1,
            }
        )

        answer_text = res["text"].strip()
        model_used = res["model"]
        duration_ms = res["duration_ms"]

        # Check if the model explicitly expressed insufficiency
        lower_ans = answer_text.lower()
        if "do not have enough information" in lower_ans or "insufficient information" in lower_ans:
            return INSUFFICIENT_MESSAGE, model_used, duration_ms, "insufficient"

        return answer_text, model_used, duration_ms, "success"


grounded_generator = GroundedGenerator()
