# VaultAI — Project Agent Instructions

## 1. Project Identity

VaultAI is a sovereign, self-hosted AI workbench being developed for SIH 2026 Problem Statement 26117 (MRPL).

The core objective is:

> Provide a local-first, air-gapped AI workbench for confidential organizational documents, grounded knowledge retrieval, controlled agent workflows, coding assistance, multimodal understanding, and real deliverables.

The system must prioritize:

- Local execution
- Data sovereignty
- Confidentiality
- Grounded answers
- Explicit abstention when evidence is insufficient
- Controlled tool execution
- Observable auditability
- Model swappability
- No unnecessary cloud dependency

The PRD.md and TRD.md in this repository are the primary product/technical references.

---

# 2. IMPORTANT: Current Implementation Status

Do NOT assume this repository is an empty starter project.

Antigravity was previously used to implement Phases 1–5.

Those phases are already present in the repository.

The current task is to continue from the existing implementation rather than rebuilding it.

Before changing anything:

1. Inspect the repository.
2. Read README.md.
3. Read PRD.md.
4. Read TRD.md.
5. Inspect backend/.
6. Inspect apps/web/.
7. Inspect tests/.
8. Understand the existing architecture.
9. Run the existing tests where practical.
10. Identify what is actually implemented versus what is only documented or mocked.

Do not rewrite working systems unnecessarily.

---

# 3. Product Architecture

The intended high-level architecture is:

User
  ↓
Next.js Frontend
  ↓
FastAPI Backend
  ↓
LangGraph Orchestrator
  ├── Document Agent
  │     └── RAG
  │           ├── Document Selection
  │           ├── Source-Constrained Retrieval
  │           └── Grounded Generation
  │
  ├── Coding Agent
  │     └── Ollama Coding Model
  │           └── Docker Sandbox
  │
  └── Vision Agent
        └── Local Vision Model

Supporting systems:

- Document storage
- Chroma vector database
- Ollama local model runtime
- Audit logging
- Docker sandbox
- Frontend API client

---

# 4. Local Models

VaultAI is intended to operate locally through Ollama.

Current local models:

### Document / general reasoning

qwen3.5:latest

### Coding

qwen2.5-coder:7b

### Vision

qwen3-vl:8b

### Legacy / prototype coding model

deepseek-coder:1.3b-instruct

Do not introduce cloud models unless explicitly requested.

Do not silently replace the local architecture with OpenAI, Anthropic, Gemini, OpenCode Zen, or another hosted provider.

The application should remain usable in an air-gapped/local environment.

---

# 5. Phase 1 — Backend Skeleton

Already implemented.

The backend uses FastAPI.

Important backend areas include:

backend/app/main.py

backend/app/config.py

backend/app/routes/

backend/app/services/

backend/app/schemas/

The backend exposes API endpoints including:

GET /api/v1/health

POST /api/v1/chat

Document-related endpoints

Sandbox execution endpoint

The backend should remain the central application API.

---

# 6. Phase 2 — RAG

Already implemented.

The RAG pipeline is one of the most important parts of VaultAI.

Current concepts:

1. Local PDF ingestion
2. PDF text extraction using PyPDF
3. Chunking
4. Sentence Transformer embeddings
5. ChromaDB vector storage
6. Document selection
7. Source-constrained retrieval
8. Grounded generation using local Ollama
9. Abstention when evidence is insufficient

Current embedding model:

all-MiniLM-L6-v2

The system uses ChromaDB for vector storage.

The intended retrieval architecture is NOT:

query → blindly search all chunks → answer

Instead it should preserve:

query
→ document selection
→ source-constrained retrieval
→ grounded generation
→ answer / abstention

Do not remove document selection merely to simplify retrieval.

Do not allow the model to invent unsupported organizational facts.

If the retrieved context does not support an answer, the system should abstain.

---

# 7. Phase 3 — LangGraph

Already implemented.

The backend contains:

backend/app/graph/

including:

- state
- router
- workflow
- nodes

Current conceptual routing:

User request
→ Router
→ Document Agent / Coding Agent / Vision Agent
→ response

The LangGraph workflow should remain the orchestration layer.

Do not replace LangGraph with an unrelated custom router unless there is a clear technical reason and the change is explicitly approved.

---

# 8. Phase 4 — Frontend Integration

Already implemented.

Frontend:

apps/web/

Technology:

- Next.js
- React
- Tailwind CSS
- Framer Motion
- Lucide

The original UI was a visual/product prototype.

It has since been connected to the backend where functionality exists.

Important:

Do not destroy or unnecessarily redesign the existing visual language.

Preserve the existing VaultAI interface unless a product requirement requires a change.

The frontend should consume actual backend data.

Do NOT reintroduce fake assistant responses, fake evidence, fake model status, fake LangGraph execution steps, or fake security telemetry.

If backend functionality is unavailable, the UI should clearly say it is unavailable rather than fabricate a successful result.

---

# 9. Phase 5 — Sandbox

Already implemented.

The coding execution system uses a Docker sandbox.

Important security properties:

- Network disabled
- Restricted CPU
- Restricted memory
- Execution timeout
- Non-root execution
- No host filesystem mounts
- No Docker socket access
- No host secrets
- No arbitrary package installation

Generated code must NOT be executed directly on the host machine.

The sandbox is the execution boundary for generated code.

Do not bypass the sandbox for convenience.

Do not execute generated code with subprocess on the host.

Do not add network access to the sandbox unless explicitly required and reviewed.

---

# 10. Auditability

An audit foundation already exists.

Audit records should be useful for observing:

- requests
- agent route
- model used
- tool/sandbox execution
- result status
- relevant execution metadata

Important:

Do not claim that security guarantees exist merely because a UI says "secure", "zero egress", or similar.

Security claims must be backed by actual implementation or observable evidence.

Do not fabricate telemetry.

---

# 11. Phase 6 — Coding Agent

Phase 6 is the next major implementation area.

The intended architecture is:

User coding request
→ LangGraph router
→ Coding Agent
→ local Qwen2.5-Coder 7B via Ollama
→ generated code
→ Docker sandbox
→ inspect execution result
→ retry/correct if necessary
→ final response

The coding agent should eventually support an agentic workflow rather than merely returning code text.

Desired conceptual loop:

PLAN
→ GENERATE
→ EXECUTE
→ INSPECT
→ CORRECT
→ EXECUTE AGAIN
→ DELIVER

The implementation should remain controlled and deterministic enough to audit.

---

# 12. Current Phase 6 Known Issues

The existing coding_agent.py was implemented as an initial Phase 6 version.

Inspect it before modifying it.

Known issues from the previous implementation include:

### Coding model heuristic

The existing implementation may reject qwen3.5 because it checks whether the configured model name contains "code" or "coder".

The intended coding model is now:

qwen2.5-coder:7b

Therefore the coding-agent model selection should eventually be explicit rather than relying on fragile string heuristics.

### Async execution

The existing coding agent may use:

asyncio.get_event_loop().run_until_complete(...)

inside a graph node.

This may be problematic when an event loop is already running.

Do not blindly preserve this pattern if it causes runtime issues.

### Retry behavior

The initial implementation may retry the same generated code rather than generating a corrected version based on sandbox feedback.

A proper Phase 6 implementation should eventually use sandbox failure output to inform a correction step.

Do not claim iterative correction exists until it actually does.

---

# 13. Coding Agent Safety Rules

Generated code must be treated as untrusted.

Never:

- execute generated code directly on the host
- give generated code unrestricted filesystem access
- give generated code network access
- expose environment secrets
- expose the Docker socket
- mount the repository into the sandbox unless explicitly designed and reviewed
- automatically install arbitrary dependencies from the internet

All execution must remain inside the controlled sandbox.

---

# 14. OpenCode Is NOT VaultAI

OpenCode was tested as an external coding assistant for repository editing.

It is NOT the VaultAI coding agent.

Do not confuse:

OpenCode
with
VaultAI Coding Agent.

VaultAI's coding agent is an application feature implemented inside:

backend/app/graph/nodes/coding_agent.py

and related services.

The VaultAI coding agent should use:

Ollama
+
qwen2.5-coder:7b
+
Docker sandbox

OpenCode is only a developer tool.

---

# 15. No Cloud Dependency

VaultAI is designed around local models.

Do not add:

- OpenAI API calls
- Anthropic API calls
- Gemini API calls
- hosted embeddings
- hosted vector databases
- telemetry services
- external AI APIs

unless explicitly requested.

Ollama should remain the model runtime.

---

# 16. Model Separation

Keep model responsibilities explicit.

Document requests:

qwen3.5:latest

Coding requests:

qwen2.5-coder:7b

Vision requests:

qwen3-vl:8b

Do not use one model for everything merely because it is easier.

The architecture is intentionally model-swappable.

---

# 17. Testing Requirements

Before declaring an implementation complete:

Run the relevant backend tests.

The repository already contains tests covering areas including:

- health
- chat
- RAG
- document selection
- retrieval
- grounding
- abstention
- LangGraph routing
- LangGraph workflow
- Ollama service
- PDF ingestion
- sandbox
- audit
- schemas

Do not delete tests just because they fail after an implementation change.

Fix the implementation or update a test only when the intended behavior has genuinely changed.

For frontend changes, run the Next.js production build where practical.

---

# 18. Development Discipline

Before modifying code:

1. Inspect existing implementation.
2. Understand dependencies.
3. Identify the smallest appropriate change.
4. Make the change.
5. Run relevant tests.
6. Run build checks when applicable.
7. Report exactly what changed.

Do not perform massive rewrites.

Do not recreate functionality that already exists.

Do not introduce unnecessary frameworks.

Do not rename large numbers of files without a strong reason.

Do not change architecture merely for stylistic preference.

---

# 19. Git Safety

Never execute:

git reset --hard

git clean -fd

or other destructive commands without explicit user approval.

Do not discard user changes.

Before large modifications, inspect:

git status

The current branch is:

frontend-integration

The current implementation has already been checkpointed and pushed to GitHub.

---

# 20. Documentation Rules

When functionality is implemented:

- Update relevant documentation if necessary.
- Do not document planned functionality as completed.
- Do not claim security properties that are not actually implemented.
- Clearly distinguish prototype behavior from production-grade security.

PRD.md and TRD.md remain the primary requirements references.

---

# 21. Current Goal

Continue development from the existing implementation.

The immediate development goal is:

PHASE 6 — CODING AGENT

But before implementing Phase 6:

1. Inspect the entire repository.
2. Read this AGENTS.md.
3. Read PRD.md and TRD.md.
4. Inspect the existing Phase 1–5 implementation.
5. Inspect existing tests.
6. Inspect backend/app/graph/nodes/coding_agent.py.
7. Inspect backend/app/services/sandbox_service.py.
8. Inspect backend/app/services/ollama_service.py.
9. Inspect backend/app/graph/workflow.py.
10. Inspect the frontend coding/sandbox integration.
11. Run the existing tests.

Do NOT modify files during this initial inspection.

After inspection, provide a concise report containing:

- Current architecture
- What Phases 1–5 actually implement
- Current Phase 6 implementation
- Phase 6 gaps
- Files that should be changed
- Tests that should be added/updated
- Recommended implementation sequence

Then WAIT for approval before modifying Phase 6.

---

# 22. Final Principle

VaultAI should be a real working local prototype, not a UI simulation.

Prefer:

REAL BACKEND
REAL LOCAL MODELS
REAL RAG
REAL TOOL EXECUTION
REAL SANDBOX
REAL AUDIT DATA
REAL TESTS

over:

FAKE STATUS
FAKE EVIDENCE
FAKE TELEMETRY
FAKE AGENT STEPS
FAKE SECURITY CLAIMS

If something is not implemented, say so clearly.