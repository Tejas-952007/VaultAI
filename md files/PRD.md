# VaultAI — Product Requirements Document (PRD)

**Version:** 2.0  
**Project:** SIH 2026 — PS 26117 (MRPL)  
**Status:** MVP-focused implementation baseline

## 1. Problem Statement

Industrial and engineering teams work with confidential PDFs, reports, SOPs, inspection records, spreadsheets, images, and technical documents. Sending this material to cloud AI services creates confidentiality and data-sovereignty concerns.

A generic chatbot is also insufficient: users need answers grounded in organizational documents, evidence showing where an answer came from, controlled agent/tool execution, useful deliverables, and observable audit/security evidence.

VaultAI is a self-hosted, local-first AI workbench for confidential organizational knowledge and controlled agent workflows.

## 2. Target User + Personas

### Primary Target User
Technical and operational employees who need to query, analyze, summarize, or act on confidential organizational information.

### Persona 1 — Engineering / Operations Analyst
- Works with technical reports, SOPs, inspection documents, manuals, and operational records.
- Needs fast answers without manually searching many documents.
- Needs evidence to verify AI answers.
- May need generated reports or structured outputs later.

### Persona 2 — Security / IT Administrator
- Responsible for keeping sensitive data inside the organization's environment.
- Needs local inference with no cloud fallback.
- Needs model provenance, audit events, and observable security controls.
- Needs confidence that code/tool execution cannot access the host unrestrictedly.

## 3. Goals and Non-Goals

### Goals
1. Run inference locally through Ollama.
2. Store confidential documents locally.
3. Build document-aware RAG with document selection before retrieval.
4. Generate grounded answers with source evidence.
5. Abstain when context is insufficient.
6. Route requests through controlled LangGraph workflows.
7. Execute code/tools only inside a restricted sandbox.
8. Expose a real FastAPI API to the frontend.
9. Record basic audit and model-provenance information.
10. Demonstrate an end-to-end local/air-gapped workflow.

### Non-Goals for MVP
- Production-scale identity management.
- Kubernetes or distributed inference.
- Enterprise SIEM integration.
- Dozens of file formats.
- Fully autonomous AI employees.
- Unrestricted host-side code execution.
- Cloud model fallback.
- Cloud-hosted RAG/vector stores.
- Perfect enterprise-grade security certification.

## 4. User Stories

- As an analyst, I want to upload a confidential PDF so that VaultAI can process it locally.
- As an analyst, I want to ask questions about uploaded documents so that I can find information quickly.
- As an analyst, I want answers to include evidence so that I can verify them.
- As an analyst, I want VaultAI to say when the documents do not contain enough information so that it does not invent an answer.
- As an analyst, I want requests routed to the appropriate agent so that document, coding, and vision tasks use suitable capabilities.
- As an administrator, I want model provenance so that I know which local model produced an answer.
- As an administrator, I want audit events so that important actions can be reviewed.
- As an administrator, I want code execution isolated from the host so that generated code cannot freely affect the workstation.

## 5. Feature Scope

### MVP
1. Local model gateway through Ollama.
2. PDF upload and local storage.
3. PDF text extraction.
4. Local embeddings and ChromaDB.
5. Document selection before retrieval.
6. Source-constrained retrieval.
7. Grounded Qwen3.5 generation.
8. Abstention for insufficient evidence.
9. Evidence/provenance in API responses.
10. FastAPI backend.
11. LangGraph routing.
12. Restricted sandbox foundation.
13. Basic audit events.
14. Frontend connection to real backend.

### V2
- Multimodal ingestion and image analysis.
- DOCX/XLSX/PPTX/CSV support.
- OCR.
- More complete plan → tools → inspect → iterate workflows.
- Word/Excel/PowerPoint/report artifact generation.
- Authentication and RBAC.
- Fine-grained document permissions.
- Rich audit/history UI.
- Stronger tool policy enforcement.

### Later
- Enterprise SSO.
- Policy engine.
- Enterprise observability/SIEM integration.
- Distributed inference.
- Model registry and lifecycle management.
- Large-scale deployment architecture.

## 6. MVP Functional Requirements

### FR-01 — Local Model Service
- Ollama is the model runtime.
- Backend uses a configurable local Ollama endpoint.
- No silent cloud fallback.
- Model name is configurable.

### FR-02 — PDF Upload
- Accept PDF files through the API.
- Store files under a controlled local data directory.
- Generate a unique document ID.
- Record filename, size, timestamp, and SHA-256.
- Reject unsafe paths and invalid uploads.

### FR-03 — Document Processing
- Extract text with PyPDF.
- Split text with a recursive text splitter.
- Generate embeddings using `all-MiniLM-L6-v2`.
- Store vectors and metadata in ChromaDB.
- Keep stable document identity in chunk metadata.

### FR-04 — Document Selection
Before retrieval, determine which documents are relevant to the question using semantic, lexical, metadata, or deterministic hybrid signals.

### FR-05 — Source-Constrained Retrieval
Retrieve chunks only from selected documents and preserve source/chunk metadata.

### FR-06 — Grounded Generation
The prompt must instruct the model to answer only from supplied context.

### FR-07 — Abstention
If evidence is absent or below a configured threshold, return an explicit insufficiency response instead of fabricating an answer.

### FR-08 — Evidence
Grounded answers expose enough information to identify their supporting document/chunk.

### FR-09 — Chat API
`POST /api/v1/chat` returns request ID, answer, route, model, evidence, and status/error information.

### FR-10 — LangGraph Router
MVP graph: `START → router → document/coding/vision agent → END`. A deterministic rule/keyword router is acceptable initially.

### FR-11 — Coding Agent Safety
The coding agent may generate code, but generated code must not execute directly on the host.

### FR-12 — Sandbox
Code/tool execution must use a restricted environment, preferably Docker, with controlled filesystem, restricted/disabled network, process/resource limits, timeout, and explicit I/O.

### FR-13 — Audit Events
Record document upload, ingestion, query, retrieval, model invocation, tool execution, and important errors.

### FR-14 — Model Provenance
Record the model/runtime used for each AI invocation.

### FR-15 — Frontend Integration
Connect the existing UI shell to the real API. Priority: Chat → Documents/upload → Evidence → basic history/audit → remaining screens.

## 7. Data Model Sketch

### User
`id`, `username`, `role`, `created_at`

### Document
`id`, `filename`, `sha256`, `size_bytes`, `mime_type`, `storage_path`, `status`, `created_at`

### DocumentChunk
`id`, `document_id`, `chunk_index`, `text`, `metadata`, `embedding_reference`

### Query
`id`, `user_id`, `question`, `route`, `status`, `created_at`

### Retrieval
`query_id`, `document_id`, `chunk_id`, `score`, `rank`

### ModelInvocation
`id`, `query_id`, `provider`, `model`, `runtime`, `duration_ms`, `status`

### ToolExecution
`id`, `query_id`, `tool`, `sandbox_id`, `status`, `duration_ms`

### Artifact
`id`, `query_id`, `type`, `path`, `sha256`

### AuditEvent
`id`, `timestamp`, `actor`, `event_type`, `resource_id`, `status`, `details`

## 8. Edge Cases and Failure States
- Unsupported/corrupt/empty PDF.
- PDF with no extractable text.
- Duplicate document.
- Embedding model unavailable.
- Chroma unavailable/corrupt.
- No relevant document.
- Insufficient retrieval evidence.
- Conflicting sources.
- Ollama/model unavailable.
- Model timeout or malformed response.
- Sandbox timeout/resource/filesystem/network failure.
- Unauthorized document access.
- Accidental external/cloud model selection.
- Frontend/backend unavailable.

Each failure should have a machine-readable API error and a useful UI state.

## 9. Success Metrics
MVP succeeds when a confidential PDF can be uploaded, stored locally, extracted, embedded, persisted in Chroma, selected before retrieval, retrieved with source constraints, answered by local Qwen3.5 through Ollama, and returned with evidence, abstention behavior, model provenance, and an audit event.

The demonstrated flow must not require cloud inference.

## 10. Open Questions
1. Exact authentication/RBAC model?
2. Required roles/document permissions?
3. Is OCR required for judging?
4. Is a vision demo required?
5. Which artifact type is the flagship deliverable?
6. Is Docker available on the demo machine?
7. What hardware is guaranteed during judging?
8. What observable network/air-gap evidence will be demonstrated?
9. Audit retention period?
10. Minimum evaluation dataset/questions?

## MVP Definition of Done

**UI → FastAPI → local PDF → PyPDF → embeddings → ChromaDB → document selection → source-constrained retrieval → local Qwen3.5/Ollama → grounded answer + evidence + provenance → UI + audit event.**

Anything beyond this must not block the core demo.
