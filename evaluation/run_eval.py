#!/usr/bin/env python3
"""Run offline RAG evaluation against the existing VaultAI pipeline.

Usage (from VaultAI-SIH-2026):

    PYTHONPATH=. python evaluation/run_eval.py

Does not write to the vector store, document store, or production source.
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.metrics import answer_relevancy, faithfulness, mean, recall_at_k  # noqa: E402
from evaluation.rag_adapter import run_existing_rag  # noqa: E402



RESULTS_DIR = ROOT / "evaluation" / "results"
DATASET_PATH = ROOT / "evaluation" / "dataset.json"


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A (judge failed; no invented score)"
    return f"{value * 100:.2f}%"


async def evaluate() -> Dict[str, Any]:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    questions: List[Dict[str, Any]] = dataset["questions"]
    rows: List[Dict[str, Any]] = []

    print(f"Evaluating {len(questions)} questions through the existing RAG pipeline...")
    for index, item in enumerate(questions, start=1):
        qid = item["id"]
        question = item["question"]
        print(f"[{index}/{len(questions)}] {qid}: {question}")

        rag = await run_existing_rag(question)
        recall = recall_at_k(rag["retrieved_chunk_ids"], item["relevant_chunk_ids"], k=5)
        faith = faithfulness(question, rag["answer"], rag["context"])
        relevancy = answer_relevancy(question, rag["answer"])

        row = {
            "id": qid,
            "question": question,
            "source_filename": item["source_filename"],
            "gold_answer_hint": item.get("gold_answer_hint"),
            "relevant_document_ids": item["relevant_document_ids"],
            "relevant_chunk_ids": item["relevant_chunk_ids"],
            "retrieved_chunk_ids": rag["retrieved_chunk_ids"],
            "retrieved_document_ids": rag["retrieved_document_ids"],
            "top5_chunks": rag["top5_chunks"],
            "retrieved_context": rag["context"],
            "generated_answer": rag["answer"],
            "pipeline_status": rag["status"],
            "pipeline_route": rag["route"],
            "model": rag["model"],
            "recall_at_5": round(recall, 4),
            "faithfulness": faith["score"],
            "faithfulness_detail": {
                "supported": faith["supported"],
                "total": faith["total"],
                "statements": faith["statements"],
                "error": faith["error"],
            },
            "answer_relevancy": relevancy["score"],
            "answer_relevancy_detail": {
                "generated_questions": relevancy["generated_questions"],
                "similarities": relevancy["similarities"],
                "error": relevancy["error"],
            },
            "latency_seconds": rag["latency_seconds"],
            "pipeline_duration_ms": rag["pipeline_duration_ms"],
            "request_id": rag["request_id"],
        }
        rows.append(row)
        print(
            f"    Recall@5={row['recall_at_5']:.2f} "
            f"Faithfulness={row['faithfulness']} "
            f"Relevancy={row['answer_relevancy']} "
            f"Latency={row['latency_seconds']:.2f}s "
            f"status={row['pipeline_status']}"
        )

    recall_avg = mean([r["recall_at_5"] for r in rows])
    faith_avg = mean([r["faithfulness"] for r in rows])
    rel_avg = mean([r["answer_relevancy"] for r in rows])
    latency_avg = mean([r["latency_seconds"] for r in rows])

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(DATASET_PATH.relative_to(ROOT)),
        "n_questions": len(rows),
        "vector_store": "ChromaDB PersistentClient (data/chroma, collection vaultai_collection, cosine HNSW)",
        "retriever": "backend.app.rag.retrieval.Retriever (RETRIEVAL_TOP_K=5)",
        "embeddings": "sentence-transformers all-MiniLM-L6-v2",
        "llm": "Ollama qwen3.5:latest via backend.app.services.ollama_service",
        "metrics_protocol": "RAGAS Faithfulness and Answer Relevancy, computed locally with Ollama + MiniLM (ragas package not used to keep evaluation air-gapped)",
        "Recall@5": recall_avg,
        "Faithfulness": faith_avg,
        "Answer Relevancy": rel_avg,
        "Average Latency seconds/query": latency_avg,
        "n_faithfulness_scored": sum(1 for r in rows if r["faithfulness"] is not None),
        "n_relevancy_scored": sum(1 for r in rows if r["answer_relevancy"] is not None),
        "headline": {
            "Recall@5": _pct(recall_avg),
            "Faithfulness": _pct(faith_avg),
            "Answer Relevancy": _pct(rel_avg),
            "Average Latency": (
                f"{latency_avg:.2f} seconds/query" if latency_avg is not None else "N/A"
            ),
        },
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {"summary": summary, "results": rows}
    json_path = RESULTS_DIR / "eval_report.json"
    csv_path = RESULTS_DIR / "eval_report.csv"
    summary_path = RESULTS_DIR / "summary.json"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "question",
                "source_filename",
                "gold_answer_hint",
                "relevant_chunk_ids",
                "retrieved_chunk_ids",
                "generated_answer",
                "pipeline_status",
                "recall_at_5",
                "faithfulness",
                "answer_relevancy",
                "latency_seconds",
                "model",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "id": row["id"],
                    "question": row["question"],
                    "source_filename": row["source_filename"],
                    "gold_answer_hint": row["gold_answer_hint"],
                    "relevant_chunk_ids": " | ".join(row["relevant_chunk_ids"]),
                    "retrieved_chunk_ids": " | ".join(row["retrieved_chunk_ids"]),
                    "generated_answer": row["generated_answer"],
                    "pipeline_status": row["pipeline_status"],
                    "recall_at_5": row["recall_at_5"],
                    "faithfulness": row["faithfulness"],
                    "answer_relevancy": row["answer_relevancy"],
                    "latency_seconds": row["latency_seconds"],
                    "model": row["model"],
                }
            )

    print("\n========== VaultAI RAG Evaluation Summary ==========")
    print(f"Recall@5: {summary['headline']['Recall@5']}")
    print(f"Faithfulness: {summary['headline']['Faithfulness']}")
    print(f"Answer Relevancy: {summary['headline']['Answer Relevancy']}")
    print(f"Average Latency: {summary['headline']['Average Latency']}")
    print(f"JSON report: {json_path}")
    print(f"CSV report:  {csv_path}")
    return report


if __name__ == "__main__":
    asyncio.run(evaluate())
