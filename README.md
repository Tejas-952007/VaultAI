# ⚡ VaultAI

**Sovereign · Local-First · Secure AI Workbench**

VaultAI is a local-first AI workbench built for organizations that need to work with sensitive documents and AI workloads while keeping their data under local control.

It combines **document intelligence, RAG, local AI models, coding assistance, vision, access control, audit logging, and controlled code execution** in one workspace.

> **Built for Smart India Hackathon 2026 — Problem Statement 26117 (MRPL)**

## 🎥 Live Demo

[▶️ Watch VaultAI Live Demo on YouTube](https://youtu.be/0AbFoRXtInE)

## Features

* 📚 Local document knowledge base
* 🔎 Retrieval-Augmented Generation (RAG)
* 🏛️ Open Knowledge Framework (OKF) for concept-based document & agent governance
* 📏 Local RAG evaluation suite (Recall@5, Faithfulness, Answer Relevancy)
* 🧠 Local AI inference using Ollama
* 🤖 Document, Coding, and Vision agents
* 💻 Coding-agent execution through Docker sandbox
* 🛡️ Role-Based Access Control (RBAC)
* 🔐 Authentication and security controls
* 📋 Audit logging for important actions
* 📊 Local CPU, memory, and GPU telemetry
* 🧾 Evidence-based and grounded responses
* 🖥️ Local-first application architecture

## Requirements

* Python 3.10+
* Node.js 18+
* PostgreSQL
* Docker
* Ollama
* NVIDIA drivers / NVIDIA SMI *(optional, for GPU telemetry)*

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/kadz23dev/VaultAI-SIH-2026.git
cd VaultAI-SIH-2026
```

### 2. Install backend dependencies

```bash
python -m venv .venv
pip install -r requirements.txt
```

Configure PostgreSQL and the required environment variables.

### 3. Start Ollama

Make sure Ollama is running locally and the required models are available.

```bash
ollama pull qwen3.5:latest
```

### 4. Start the backend

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 5. Start the frontend

```bash
cd apps/web
npm install
npm run dev
```

The frontend normally runs at:

```text
http://127.0.0.1:3001
```

## How to Use VaultAI

### 1. Workbench

Use the Workbench to interact with the local AI system and access the available AI workflows.

### 2. Knowledge Base

Upload documents and use them as a source for knowledge-based questions.

VaultAI processes the document through:

```text
Document → Chunking → Embeddings → Retrieval → Grounded Answer
```

### 3. Coding Agent

Ask the Coding Agent for code generation or analysis.

Generated code can be executed through the Docker sandbox rather than directly inside the main application.

### 4. Vision Agent

Use the Vision Agent for supported image-based AI tasks using a local vision model.

### 5. Access Control

Administrators can manage roles and permissions through the Access Control section.

### 6. Security & Audit

The Security Hub provides visibility into implemented and observable security controls, while audit history records important system activities.

### 7. Control Manager

View local system telemetry such as CPU, memory, GPU usage, and application resource usage.

### 8. Open Knowledge Framework (OKF)

VaultAI implements the **Open Knowledge Framework (OKF)** to govern industrial documents and agent behaviors through explicit concept schemas (`okf/concepts/`):
* **Document Concepts:** Standardizes technical document types (such as `P&ID`, `SOP`, and `Engineering Reports`) with classification metadata, sensitivity ratings, and role-based clearance.
* **Access Filtering:** Automatically filters out unauthorized documents prior to RAG selection based on employee role clearance (e.g., Administrator, Engineer, Analyst, Technician).
* **Agent Governance:** Constrains agent access, output grounding requirements, and sandbox enforcement.

### 9. Local RAG Evaluation Suite

A local, air-gapped evaluation framework based on RAGAS definitions, measuring retrieval and generation quality against domain documents without relying on external cloud APIs:
* **Metrics:** Evaluates **Recall@K**, **Faithfulness** (claim grounding vs. retrieved context), **Answer Relevancy** (reverse question similarity via local embeddings), and **Latency**.
* **Running Evaluation:**

```bash
PYTHONPATH=. python evaluation/run_eval.py
```

Results are saved to `evaluation/results/` as both JSON reports and CSV summaries.

## Local AI Models

VaultAI currently supports configured local models such as:

| Purpose            | Model              |
| ------------------ | ------------------ |
| Document / General | `qwen3.5:latest`   |
| Coding             | `qwen2.5-coder:7b` |
| Vision             | `qwen3-vl:8b`      |

Models are executed through **Ollama**.

## Technology

* **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS
* **Backend:** Python, FastAPI
* **AI:** Ollama, Qwen models
* **RAG & Evaluation:** ChromaDB, sentence-transformers (`all-MiniLM-L6-v2`), local RAGAS metrics
* **Governance:** Open Knowledge Framework (OKF)
* **Database:** PostgreSQL
* **Workflow:** LangGraph
* **Sandbox:** Docker
* **Monitoring:** PSUTIL, NVIDIA SMI

## Project Structure

```text
VaultAI-SIH-2026/
│
├── apps/web/        # Next.js frontend
├── backend/         # FastAPI backend
├── docker/          # Docker sandbox
├── okf/             # Open Knowledge Framework (document, agent & role concepts)
├── evaluation/      # Local RAG evaluation suite, dataset & benchmark reports
├── alembic/         # Database migrations
├── tests/           # Automated tests
│
├── PRD.md
├── TRD.md
├── MVP_ACCEPTANCE.md
└── README.md
```

## Prototype Status

This repository contains the **SIH 2026 working prototype** of VaultAI.

The current implementation focuses on demonstrating:

* Local AI workflows
* Document-grounded RAG with source-constrained retrieval
* Open Knowledge Framework (OKF) concept-based access control
* Offline, air-gapped RAG evaluation benchmarking
* Agent routing (Document, Coding, Vision)
* RBAC and authentication
* Security monitoring
* Auditability
* Controlled code execution
* Local system telemetry

Some production-scale capabilities such as enterprise deployment automation, advanced infrastructure hardening, and large-scale distributed execution can be extended in future versions.

## SIH 2026

**Problem Statement:** 26117
**Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)
**Project:** VaultAI

> **Your Data. Your Models. Your Control.**
