# VaultAI — Technical Requirements Document (TRD)

**Version:** 2.0  
**Status:** MVP implementation baseline  
**Project:** SIH 2026 — PS 26117 (MRPL)

## 1. Technical Objective

Build a practical local-first AI workbench where confidential organizational data remains inside the controlled environment.

Priorities:
- local inference
- local document storage
- grounded retrieval
- controlled agent routing
- sandboxed execution
- provenance
- auditability
- observable security evidence

## 2. Architecture

```text
Next.js Frontend
       |
       v
FastAPI Backend
       |
       +--------------------+
       |                    |
       v                    v
  LangGraph Router      Audit Store
       |
       +---------+---------+
       |         |         |
       v         v         v
 Document    Coding      Vision
  Agent       Agent       Agent
       |
       v
 Document Selection
       |
       v
 Source-Constrained Retrieval
       |
       v
 ChromaDB <--- all-MiniLM-L6-v2
       |
       v
 Ollama
       +--> Qwen3.5
       +--> DeepSeek-Coder 1.3B Instruct
       +--> Qwen3-VL:8B (if available)

Coding/Tool Path
       |
       v
Restricted Sandbox / Docker
```

## 3. Technology Stack

### Frontend
Next.js 14, React 18, Tailwind CSS, Framer Motion, Lucide.

### Backend
Python, FastAPI, Pydantic, Uvicorn.

### AI Runtime
Ollama. Qwen3.5 for document/text generation; DeepSeek-Coder 1.3B Instruct for coding; Qwen3-VL:8B for vision when available.

### RAG
PyPDF, LangChain text splitters, Sentence Transformers, `all-MiniLM-L6-v2`, ChromaDB, scikit-learn where useful.

### Orchestration
LangGraph.

### Sandbox
Docker preferred. No unrestricted host-side code execution.

## 4. Repository Structure

```text
VaultAI/
├── apps/web/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── rag/
│   │   ├── models/
│   │   ├── tools/
│   │   ├── sandbox/
│   │   └── audit/
│   └── tests/
├── data/{documents,chroma,artifacts,audit}/
├── docker/
├── prototype/ai-model/
└── docs/
```

`prototype/ai-model` is reference/prototype code. Production code belongs under `backend/app`.

## 5. API Requirements

### Health
`GET /api/v1/health`

Returns service availability and basic runtime status.

### Chat
`POST /api/v1/chat`

Example request:
```json
{
  "message": "What does the uploaded document say about ...?",
  "document_ids": []
}
```

Example response:
```json
{
  "request_id": "uuid",
  "answer": "...",
  "route": "document",
  "model": "qwen3.5:latest",
  "evidence": [
    {
      "document_id": "...",
      "source": "...",
      "chunk_id": "...",
      "score": 0.82
    }
  ],
  "status": "success"
}
```

### Upload
Target: `POST /api/v1/documents`

Requirements: multipart upload, PDF validation, local storage, SHA-256, document ID, ingestion status.

### Audit
Target: `GET /api/v1/audit`

Initially this may be read-only and restricted once authentication exists.

## 6. RAG Technical Requirements

### Ingestion
`validate → hash → store → extract → split → embed → persist → ready`

Metadata must include stable `document_id`.

Use one configured Chroma collection. Do not retain the prototype's collection-name inconsistency.

### Document Selection
Selection happens before final retrieval. Candidate signals may include semantic similarity, lexical overlap, metadata, and deterministic rules.

Avoid query-specific hardcoded phrase bonuses.

### Retrieval
1. Embed query.
2. Select candidate documents.
3. Retrieve top-K chunks only from selected documents.
4. Preserve source metadata.
5. Apply evidence threshold.
6. Pass only selected evidence to generation.

### Grounding
Prompt must require:
- answer only from supplied context
- no invented facts
- explicit insufficiency when evidence is missing
- source attribution where possible

## 7. Model Gateway

Create one backend abstraction around Ollama.

Responsibilities:
- endpoint configuration
- model selection
- timeout
- generation parameters
- health check
- error normalization
- provenance capture

Do not scatter raw Ollama calls throughout the application. No silent cloud provider calls.

## 8. LangGraph Requirements

Initial graph:

```text
START
  |
router
  |
  +--> document_agent
  +--> coding_agent
  +--> vision_agent
  |
END
```

State should eventually include request ID, input, route, selected documents, evidence, model invocation, tool executions, answer, artifacts, and errors.

Start simple and expand only when required.

## 9. Sandbox Requirements

The sandbox is a security boundary, not a UI feature.

At minimum:
- isolated filesystem/workspace
- no arbitrary host paths
- restricted/disabled network
- execution timeout
- CPU/memory limits
- controlled environment variables
- controlled input/output
- cleanup after execution

Never execute model-generated Python directly through the backend host interpreter.

## 10. Security Requirements

### Locality
All demonstrated document processing and inference remains local.

### Network
For an air-gapped demonstration, external network should be disabled or physically disconnected where possible. No cloud model fallback and no telemetry dependency.

Security UI must report measured/verified state, not hardcoded claims.

### File Safety
Sanitize filenames, prevent path traversal, use generated storage paths, validate file type, and hash uploads.

### Secrets
Never hardcode credentials. Use environment/configuration management.

### Audit
Record actor, event type, resource, timestamp, status, and relevant metadata.

## 11. Performance Requirements

MVP is functional rather than enterprise-scale.

- Reuse model/embedding instances.
- Avoid loading all embeddings into RAM for every query.
- Avoid blocking the API event loop with long operations without an appropriate strategy.
- Use request IDs.
- Return useful timeout/error states.
- Support one realistic demo workload reliably.

## 12. Observability

Log enough to debug:
- request ID
- route
- document IDs
- retrieval count
- model name
- duration
- status
- errors

Do not unnecessarily log document contents or sensitive prompts.

## 13. Testing Requirements

### Unit
File validation, hashing, chunk metadata, document selection, retrieval filtering, grounding/abstention, router classification, sandbox policy.

### Integration
Upload → ingest; query → retrieve → generate; backend → Ollama; frontend → backend.

### Security
Path traversal, unsupported/oversized files, sandbox network access, sandbox filesystem access, model provenance, cloud fallback absence.

## 14. Technical Constraints

- Must work with available local hardware.
- Core demo cannot depend on cloud inference.
- No Kubernetes.
- No distributed systems.
- Architecture must remain understandable and debuggable during SIH judging.

## 15. Technical Definition of Done

1. API starts cleanly.
2. Health endpoint works.
3. PDF upload works.
4. Ingestion persists locally.
5. Chroma contains chunks.
6. Document selection precedes retrieval.
7. Retrieval is source-constrained.
8. Ollama produces a local response.
9. Evidence is returned.
10. Insufficient context causes abstention.
11. Model provenance is captured.
12. Frontend consumes the real API.
13. Basic audit events are persisted.
14. Generated code cannot execute unrestricted on the host.
