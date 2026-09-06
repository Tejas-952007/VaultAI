# VaultAI — Implementation Guide

## 1. Implementation Order

```text
Backend contract
    ↓
Ollama wrapper
    ↓
PDF ingestion
    ↓
Chroma + embeddings
    ↓
Document selection
    ↓
Source-constrained retrieval
    ↓
Grounded generation
    ↓
Evidence + abstention
    ↓
LangGraph
    ↓
Sandbox
    ↓
Frontend integration
    ↓
Security validation
```

## 2. Backend Layering

```text
routes/     HTTP only
schemas/    request/response contracts
services/   application orchestration
rag/        ingestion, selection, retrieval
models/     Ollama abstraction
agents/     LangGraph nodes
tools/      tool definitions
sandbox/    isolated execution
audit/      audit persistence
```

Routes should not contain the full RAG/model implementation.

## 3. Model Wrapper

Create one service for Ollama calls. It accepts model, prompt/system prompt, and generation options; returns generated text, model, duration, and status.

All callers use this wrapper.

## 4. Ingestion

For every PDF:

`validate → hash → store → extract → split → embed → persist → ready`

Every chunk must retain stable `document_id` metadata.

Use one configured Chroma collection. Fix the prototype's collection-name inconsistency.

## 5. Document Selection

The selector answers:

> Which documents should be allowed to contribute evidence to this query?

Retrieval then operates only within that set.

Avoid hardcoded demo-specific phrase bonuses.

## 6. Retrieval

Return:
- `document_id`
- `chunk_id`
- `source`
- `score`
- `text`
- `metadata`

Generation receives only selected evidence.

## 7. Grounded Answering

Prompt contract:
- answer from supplied context
- do not invent facts
- explicitly state insufficiency
- do not use outside knowledge as evidence
- identify sources

API should distinguish grounded success, insufficient evidence, and system failure.

## 8. LangGraph

Keep state explicit:

```text
request_id
input
route
selected_documents
evidence
model_provenance
tool_results
answer
artifacts
error
```

Do not add complex planning loops until the simple graph is stable.

## 9. Sandbox

Never execute generated code with host `exec()`.

Use an isolated runner with timeout, resource limits, filesystem restrictions, network restrictions, and cleanup.

## 10. Frontend

The existing UI is the visual shell.

Replace mock data progressively:
1. chat response
2. evidence
3. document list/upload
4. model status
5. history/audit

Keep the existing visual language.

## 11. Error Contract

Example:

```json
{
  "request_id": "uuid",
  "status": "error",
  "code": "MODEL_UNAVAILABLE",
  "message": "Local model service is unavailable."
}
```

Never expose stack traces to normal users.

## 12. Configuration

Use environment variables for API host/port, Ollama URL, document directory, Chroma directory, collection name, model names, timeouts, retrieval thresholds, and sandbox settings.

Provide `.env.example`.

## 13. Prototype Migration

Useful prototype concepts:
- document selection
- PyPDF extraction
- embeddings
- Chroma persistence
- grounded Qwen prompt
- LangGraph routing

Fix before production:
- collection-name mismatch
- hardcoded paths
- hardcoded phrase bonuses
- scattered Ollama calls
- interactive vision `input()`
- lack of structured API
- lack of sandbox
- lack of provenance/audit

## 14. Testing Strategy

Priority:
1. unit tests for pure logic
2. integration tests with local dependencies
3. one real end-to-end smoke test
4. security boundary tests

Keep a fixed set of representative documents/questions.

## 15. Demo Workflow

1. Start Ollama.
2. Start backend.
3. Start frontend.
4. Upload confidential engineering PDF.
5. Show local document status.
6. Ask a factual question.
7. Show selected source/evidence.
8. Show local Qwen3.5 provenance.
9. Ask an unsupported question.
10. Show abstention.
11. Show audit event.

Only after this is reliable should the larger agentic workflow be added.
