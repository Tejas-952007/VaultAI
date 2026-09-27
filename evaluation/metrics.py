"""RAGAS-style metrics computed locally with VaultAI's Ollama + embeddings.

RAGAS itself is not added as a production dependency: it pulls cloud LLM
clients and conflicts with this project's local-only model allowlist.
These implementations follow the published RAGAS definitions:

- Recall@K: |relevant ∩ retrieved@K| / |relevant|
- Faithfulness: fraction of answer statements supported by retrieved context
- Answer Relevancy: mean cosine similarity between the original question and
  questions reverse-generated from the answer (RAGAS AnswerRelevancy)
"""

from __future__ import annotations

import json
import math
import re
from typing import Any, Dict, List, Optional, Sequence

from backend.app.rag.vector_store import vector_store
from backend.app.services.ollama_service import ollama_service

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def recall_at_k(retrieved_ids: Sequence[str], relevant_ids: Sequence[str], k: int = 5) -> float:
    if not relevant_ids:
        return 0.0
    retrieved = list(retrieved_ids)[:k]
    hits = len(set(retrieved) & set(relevant_ids))
    return hits / len(set(relevant_ids))


def _parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = _JSON_OBJECT_RE.search(cleaned)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _judge(prompt: str) -> Dict[str, Any]:
    result = ollama_service.generate(
        prompt=prompt,
        system_prompt=(
            "You are a strict evaluation judge for a RAG system. "
            "Reply with a single JSON object only. No markdown. No extra text."
        ),
        options={"num_predict": 400, "temperature": 0.0},
    )
    parsed = _parse_json_object(result.get("text", ""))
    if parsed is None:
        raise ValueError(f"Judge did not return JSON: {result.get('text', '')[:400]}")
    return parsed


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def faithfulness(question: str, answer: str, context: str) -> Dict[str, Any]:
    """RAGAS Faithfulness: supported statements / total statements."""
    if not (answer or "").strip():
        return {"score": 0.0, "statements": [], "supported": 0, "total": 0, "error": None}

    prompt = (
        "Decompose the ANSWER into atomic factual statements. "
        "For each statement, set supported=true only if the CONTEXT fully supports it. "
        "Do not use outside knowledge.\n"
        "If the answer only says there is not enough information, treat that as one statement "
        "and set supported=true only when the CONTEXT does not contain a direct answer to QUESTION.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"ANSWER:\n{answer}\n\n"
        'Return JSON: {"statements": [{"text": "...", "supported": true}]}'
    )
    try:
        parsed = _judge(prompt)
        statements = parsed.get("statements") or []
        total = len(statements)
        supported = sum(1 for s in statements if s.get("supported") is True)
        score = (supported / total) if total else 0.0
        return {
            "score": round(score, 4),
            "statements": statements,
            "supported": supported,
            "total": total,
            "error": None,
        }
    except Exception as exc:
        return {
            "score": None,
            "statements": [],
            "supported": 0,
            "total": 0,
            "error": str(exc),
        }


def answer_relevancy(question: str, answer: str) -> Dict[str, Any]:
    """RAGAS Answer Relevancy via reverse questions + MiniLM cosine."""
    if not (answer or "").strip():
        return {"score": 0.0, "generated_questions": [], "similarities": [], "error": None}

    prompt = (
        "Generate 3 questions that the ANSWER would be a reasonable response to. "
        "Questions must be answerable from the ANSWER itself.\n\n"
        f"ANSWER:\n{answer}\n\n"
        'Return JSON: {"questions": ["...", "...", "..."]}'
    )
    try:
        parsed = _judge(prompt)
        generated = [q for q in (parsed.get("questions") or []) if isinstance(q, str) and q.strip()]
        if not generated:
            raise ValueError("Judge returned no reverse questions")

        embeddings = vector_store.embed_texts([question, *generated])
        q_vec = embeddings[0]
        similarities = [_cosine(q_vec, embeddings[i + 1]) for i in range(len(generated))]
        score = sum(similarities) / len(similarities)
        return {
            "score": round(float(score), 4),
            "generated_questions": generated,
            "similarities": [round(s, 4) for s in similarities],
            "error": None,
        }
    except Exception as exc:
        return {
            "score": None,
            "generated_questions": [],
            "similarities": [],
            "error": str(exc),
        }


def mean(values: List[Optional[float]]) -> Optional[float]:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present) / len(present)
