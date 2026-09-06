# ⚡ VaultAI

**Sovereign · Local-First · Secure AI Workbench**

VaultAI is a local-first AI workbench built for organizations that need to work with sensitive documents and AI workloads while keeping their data under local control.

It combines **document intelligence, RAG, local AI models, coding assistance, vision, access control, audit logging, and controlled code execution** in one workspace.

> **Built for Smart India Hackathon 2026 — Problem Statement 26117 (MRPL)**

## Features

* 📚 Local document knowledge base
* 🔎 Retrieval-Augmented Generation (RAG)
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
* **RAG:** ChromaDB, embeddings, document retrieval
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
* Document-grounded RAG
* Agent routing
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
