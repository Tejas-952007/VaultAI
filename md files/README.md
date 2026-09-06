# VaultAI

VaultAI is a local-first AI workbench for confidential organizational knowledge and controlled agent workflows.

## Core Principle

**Confidential data stays inside the controlled environment.**

The project is intentionally MVP-first. The primary engineering goal is a real, testable local RAG workflow rather than a large collection of simulated enterprise features.

## MVP Flow

```text
Browser → Next.js → FastAPI → PDF ingestion → PyPDF
→ all-MiniLM-L6-v2 → ChromaDB → document selection
→ source-constrained retrieval → Ollama/Qwen3.5
→ evidence + provenance → Browser
```

## Repository

- `apps/web` — frontend
- `backend` — production API/application
- `prototype/ai-model` — original AI prototype/reference
- `data` — local runtime data
- `docs` — project documentation

## Documentation

- `PRD.md` — product requirements
- `TRD.md` — technical requirements
- `plan.md` — implementation phases
- `task.md` — task board
- `implementation.md` — engineering guide
- `MVP_ACCEPTANCE.md` — acceptance/demo checklist

## Important Rule

Do not present mocked UI states as implemented backend capabilities.

A feature is complete only when behavior is real, testable, and connected to the system.

## Security Position

Security claims should be based on observable behavior:
- local model runtime
- local storage
- no cloud fallback
- restricted sandbox
- model provenance
- audit events

UI labels alone are not security evidence.
