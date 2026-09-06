# VaultAI — Implementation Plan

## Principle

Build the smallest real end-to-end system first, then harden and expand.

## Phase 0 — Baseline
- Preserve existing UI as product shell.
- Separate prototype AI code from production backend.
- Establish one repository structure.
- Remove fake success states from connected paths.
- Verify Python, Node, Ollama, and GPU.

**Exit:** repository is clean and runnable.

## Phase 1 — Backend Skeleton
Build FastAPI, configuration, health endpoint, schemas, chat contract, and tests.

**Exit:** frontend/backend communicate over HTTP.

## Phase 2 — Local Models
Build Ollama wrapper, model configuration, Qwen3.5 generation, health, provenance, timeout/error handling.

**Exit:** backend makes a verified local Qwen request.

## Phase 3 — RAG
Implement:
1. PDF upload
2. local storage
3. SHA-256
4. PyPDF extraction
5. chunking
6. local embeddings
7. Chroma persistence
8. document selection
9. source-constrained retrieval
10. grounded generation
11. evidence
12. abstention

**Exit:** upload → question → grounded answer works end-to-end.

## Phase 4 — LangGraph
Build request state, router, document agent, coding agent, vision interface, and structured result propagation.

**Exit:** requests route through the graph.

## Phase 5 — Tools and Sandbox
Build tool interface, sandbox runner, filesystem/network policy, timeout/resource limits, and execution audit.

**Exit:** code/tool execution is isolated and demonstrable.

## Phase 6 — Frontend Connection
Connect existing UI to health, chat, upload, evidence, provenance, and basic history/audit.

**Exit:** visible demo is driven by real backend data.

## Phase 7 — Air-Gap Validation
Verify local model runtime, local storage/embeddings/vector store, absence of cloud fallback, and observable network behavior.

**Exit:** security claims are backed by evidence.

## Phase 8 — Hardening
As time allows: authentication, RBAC, document permissions, richer audit, artifact generation, duplicate detection, ingestion status, cleanup policies.

## Phase 9 — Evaluation and Demo
Prepare representative PDF, known questions, abstention question, provenance demonstration, sandbox restriction demonstration, audit trail, and offline evidence.

## Priority Rule

**RAG end-to-end > frontend integration > agent breadth > artifact breadth > enterprise features.**

Do not sacrifice a working grounded demo for many incomplete features.
