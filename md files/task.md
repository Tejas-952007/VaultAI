# VaultAI — Task Board

## P0 — Must Finish

### Backend
- [ ] FastAPI starts
- [ ] `/api/v1/health`
- [ ] `/api/v1/chat`
- [ ] `/api/v1/documents`
- [ ] Pydantic schemas
- [ ] environment configuration
- [ ] request IDs
- [ ] consistent errors

### Ollama
- [ ] connectivity check
- [ ] Qwen3.5 local generation
- [ ] configurable model
- [ ] timeout handling
- [ ] model provenance

### RAG
- [ ] PDF validation
- [ ] local storage
- [ ] SHA-256
- [ ] PyPDF extraction
- [ ] chunking
- [ ] all-MiniLM-L6-v2 embeddings
- [ ] Chroma persistence
- [ ] document selection
- [ ] source-constrained retrieval
- [ ] grounded prompt
- [ ] abstention
- [ ] evidence metadata

### Frontend
- [ ] real chat API
- [ ] real document upload
- [ ] real evidence
- [ ] real model provenance
- [ ] remove fake data from connected flows
- [ ] loading/error states

### Testing
- [ ] health test
- [ ] upload test
- [ ] ingestion test
- [ ] retrieval test
- [ ] grounding/abstention test
- [ ] Ollama integration test
- [ ] frontend/backend smoke test

## P1 — Strong Demo Value
- [ ] LangGraph router
- [ ] document agent
- [ ] coding agent
- [ ] vision interface
- [ ] sandbox runner
- [ ] sandbox timeout
- [ ] sandbox network restriction
- [ ] sandbox filesystem restriction
- [ ] audit events
- [ ] basic audit UI

## P2 — If Time Allows
- [ ] DOCX
- [ ] XLSX/CSV
- [ ] PPTX
- [ ] OCR
- [ ] multimodal flow
- [ ] artifact generation
- [ ] richer history
- [ ] authentication
- [ ] RBAC
- [ ] document-level permissions

## P3 — Do Not Block MVP
- [ ] SSO
- [ ] enterprise SIEM
- [ ] Kubernetes
- [ ] distributed inference
- [ ] model registry
- [ ] enterprise policy engine
- [ ] large-scale observability

## Definition of Done

A task is not done because a UI element exists.

It is done only when the backend behavior is real, testable, error-handled, and the UI does not claim an unimplemented capability.
