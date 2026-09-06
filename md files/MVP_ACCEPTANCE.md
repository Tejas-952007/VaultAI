# VaultAI — MVP Acceptance & Demo Checklist

## Environment
- [ ] Ollama installed and running
- [ ] Required local model available
- [ ] Python environment works
- [ ] Backend starts
- [ ] Frontend starts
- [ ] No cloud model dependency

## End-to-End RAG
- [ ] Upload representative PDF
- [ ] Document receives ID
- [ ] SHA-256 recorded
- [ ] File stored locally
- [ ] Text extraction succeeds
- [ ] Chunks persist
- [ ] Embeddings generated locally
- [ ] Chroma contains document
- [ ] Query selects relevant document(s)
- [ ] Retrieval restricted to selected documents
- [ ] Qwen3.5 answers from evidence
- [ ] Evidence is shown
- [ ] Model provenance is shown
- [ ] Audit event is created

## Abstention
Ask a question whose answer is absent from the uploaded document.

Expected:
- [ ] No invented answer
- [ ] Clear insufficient-evidence state
- [ ] Structured response

## Security
- [ ] No cloud fallback
- [ ] No external model endpoint
- [ ] Generated code is not executed on host
- [ ] Sandbox blocks unauthorized filesystem access
- [ ] Sandbox blocks/restricts network
- [ ] Security dashboard values come from real checks

## Demo Story

### Scene 1 — Confidentiality
Explain that the document is processed locally.

### Scene 2 — Grounded Intelligence
Upload the document and ask a known question. Show source, evidence, answer, and local model provenance.

### Scene 3 — Trust
Ask an unsupported question and show abstention.

### Scene 4 — Control
Show audit/provenance and, if implemented, sandbox restrictions.

## Defensible MVP Claim

> VaultAI provides a local, document-grounded AI workflow with source evidence, model provenance, abstention, and controlled execution boundaries.

Do not claim enterprise-grade security, complete RBAC, full multimodal support, or autonomous agents unless actually implemented and tested.
